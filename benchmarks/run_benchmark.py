"""Mesure comparative de la RAM et du CPU : notre navigateur, Chrome et Edge.

Protocole (détaillé dans benchmarks/README.md) :
  1. lancer le navigateur avec un profil temporaire vierge et tous les sites de
     sites.txt ouverts en onglets ;
  2. attendre la fin du chargement (LOAD_TIME) ;
  3. échantillonner l'arbre de processus pendant MEASURE_TIME : mémoire propre (USS)
     et temps CPU cumulé ;
  4. fermer le navigateur, recommencer RUNS fois, garder la médiane.

Usage : uv run python benchmarks/run_benchmark.py [--browsers chrome,edge] [--runs 3]
"""

import argparse
import contextlib
import io
import json
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

import psutil

SITES_FILE = Path(__file__).with_name("sites.txt")
MIB = 1024 * 1024

# Emplacements habituels des navigateurs de comparaison, par OS.
KNOWN_PATHS: dict[str, list[str]] = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "google-chrome",
        "google-chrome-stable",
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "microsoft-edge",
        "microsoft-edge-stable",
    ],
}


@dataclass
class Sample:
    """Un relevé de l'arbre de processus à un instant donné."""

    uss_bytes: int
    rss_bytes: int
    process_count: int


@dataclass
class RunResult:
    """Résultat d'une passe de mesure pour un navigateur."""

    mean_uss_mib: float
    peak_uss_mib: float
    mean_rss_mib: float
    cpu_percent: float
    process_count: int


def read_sites(path: Path) -> list[str]:
    """Lit la liste des sites en ignorant lignes vides et commentaires."""
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def find_browser(name: str) -> str | None:
    """Retourne le chemin de l'exécutable du navigateur, ou None s'il est introuvable."""
    for candidate in KNOWN_PATHS.get(name, []):
        if Path(candidate).is_file():
            return candidate
        found = shutil.which(candidate)
        if found:
            return found
    return None


def build_command(name: str, executable: str, profile_dir: Path, urls: Sequence[str]) -> list[str]:
    """Construit la ligne de commande qui ouvre les sites dans un profil vierge."""
    if name == "navigateur":
        # Notre navigateur : profil off-the-record, aucun dossier de profil nécessaire.
        return [executable, "-m", "navigateur", *urls]
    return [
        executable,
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--new-window",
        *urls,
    ]


def cpu_percent(cpu_seconds_by_pid: dict[int, tuple[float, float]], duration: float) -> float:
    """CPU moyen (en % d'un cœur) à partir des temps CPU (début, fin) de chaque processus."""
    used = sum(end - start for start, end in cpu_seconds_by_pid.values())
    return 100 * used / duration if duration > 0 else 0.0


def summarize_run(samples: Sequence[Sample], cpu: float) -> RunResult:
    """Résume les relevés d'une passe."""
    return RunResult(
        mean_uss_mib=statistics.fmean(s.uss_bytes for s in samples) / MIB,
        peak_uss_mib=max(s.uss_bytes for s in samples) / MIB,
        mean_rss_mib=statistics.fmean(s.rss_bytes for s in samples) / MIB,
        cpu_percent=cpu,
        process_count=max(s.process_count for s in samples),
    )


def median_result(runs: Sequence[RunResult]) -> RunResult:
    """Médiane champ par champ de plusieurs passes (robuste aux passes aberrantes)."""
    return RunResult(
        mean_uss_mib=statistics.median(r.mean_uss_mib for r in runs),
        peak_uss_mib=statistics.median(r.peak_uss_mib for r in runs),
        mean_rss_mib=statistics.median(r.mean_rss_mib for r in runs),
        cpu_percent=statistics.median(r.cpu_percent for r in runs),
        process_count=round(statistics.median(r.process_count for r in runs)),
    )


def format_table(results: dict[str, RunResult]) -> str:
    """Tableau Markdown, prêt à coller dans une PR ou un commit."""
    lines = [
        "| Navigateur | RAM moy. (USS) | RAM pic (USS) | RSS moy. | CPU moy. | Processus |",
        "| ---------- | -------------: | ------------: | -------: | -------: | --------: |",
    ]
    for name, r in results.items():
        lines.append(
            f"| {name} | {r.mean_uss_mib:.0f} Mio | {r.peak_uss_mib:.0f} Mio "
            f"| {r.mean_rss_mib:.0f} Mio | {r.cpu_percent:.1f} % | {r.process_count} |"
        )
    return "\n".join(lines)


def process_tree(root: psutil.Process) -> list[psutil.Process]:
    """Le processus racine et tous ses descendants encore vivants."""
    try:
        return [root, *root.children(recursive=True)]
    except psutil.NoSuchProcess:
        return []


def take_sample(processes: Iterable[psutil.Process]) -> tuple[Sample, dict[int, float]]:
    """Mémoire totale de l'arbre et temps CPU cumulé de chaque processus."""
    uss = rss = count = 0
    cpu_by_pid: dict[int, float] = {}
    for proc in processes:
        try:
            info = proc.memory_full_info()
            times = proc.cpu_times()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue  # processus terminé entre-temps : ignoré
        uss += info.uss
        rss += info.rss
        count += 1
        cpu_by_pid[proc.pid] = times.user + times.system
    return Sample(uss, rss, count), cpu_by_pid


def stop_tree(root: psutil.Process) -> None:
    """Ferme le navigateur et tous ses processus enfants."""
    tree = process_tree(root)
    for proc in tree:
        with contextlib.suppress(psutil.NoSuchProcess):
            proc.terminate()
    _, alive = psutil.wait_procs(tree, timeout=10)
    for proc in alive:
        with contextlib.suppress(psutil.NoSuchProcess):
            proc.kill()


def run_once(
    command: list[str], load_time: float, measure_time: float, interval: float
) -> RunResult:
    """Une passe : lancement, chargement, mesure, fermeture."""
    root = psutil.Process(subprocess.Popen(command).pid)
    try:
        time.sleep(load_time)
        samples: list[Sample] = []
        cpu_window: dict[int, tuple[float, float]] = {}
        start = time.monotonic()
        while time.monotonic() - start < measure_time:
            sample, cpu_by_pid = take_sample(process_tree(root))
            samples.append(sample)
            for pid, seconds in cpu_by_pid.items():
                first = cpu_window.get(pid, (seconds, seconds))[0]
                cpu_window[pid] = (first, seconds)
            time.sleep(interval)
        duration = time.monotonic() - start
    finally:
        stop_tree(root)
    if not samples or samples[-1].process_count == 0:
        raise RuntimeError("Le navigateur s'est fermé pendant la mesure.")
    return summarize_run(samples, cpu_percent(cpu_window, duration))


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Options de la ligne de commande."""
    parser = argparse.ArgumentParser(description="Mesure RAM/CPU comparative.")
    parser.add_argument("--browsers", default="chrome,edge", help="liste : navigateur,chrome,edge")
    parser.add_argument("--runs", type=int, default=3, help="nombre de passes par navigateur")
    parser.add_argument("--load-time", type=float, default=45, help="attente du chargement (s)")
    parser.add_argument("--measure-time", type=float, default=60, help="durée de mesure (s)")
    parser.add_argument("--interval", type=float, default=2, help="intervalle des relevés (s)")
    parser.add_argument("--json", type=Path, help="enregistrer aussi les résultats en JSON")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Mesure chaque navigateur demandé et affiche le tableau comparatif."""
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args(sys.argv[1:] if argv is None else argv)
    urls = read_sites(SITES_FILE)
    results: dict[str, RunResult] = {}
    for name in args.browsers.split(","):
        executable = sys.executable if name == "navigateur" else find_browser(name)
        if executable is None:
            print(f"{name} : introuvable, ignoré.", file=sys.stderr)
            continue
        runs = []
        for index in range(args.runs):
            print(f"{name} : passe {index + 1}/{args.runs}…", flush=True)
            with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
                command = build_command(name, executable, Path(profile), urls)
                runs.append(run_once(command, args.load_time, args.measure_time, args.interval))
        results[name] = median_result(runs)
    if not results:
        print("Aucun navigateur mesuré.", file=sys.stderr)
        return 1
    print()
    print(
        f"{len(urls)} sites, médiane de {args.runs} passe(s), {psutil.cpu_count()} cœurs logiques"
    )
    print(format_table(results))
    if args.json:
        payload = {name: asdict(result) for name, result in results.items()}
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
