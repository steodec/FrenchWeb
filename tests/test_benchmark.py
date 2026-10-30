"""Tests des calculs du benchmark (sans lancer de navigateur)."""

from pathlib import Path

import pytest
from run_benchmark import (
    MIB,
    SITES_FILE,
    RunResult,
    Sample,
    build_command,
    cpu_percent,
    format_table,
    median_result,
    read_sites,
    summarize_run,
)


def test_read_sites_ignores_comments_and_blank_lines(tmp_path: Path) -> None:
    sites = tmp_path / "sites.txt"
    sites.write_text("# commentaire\n\nhttps://a.example\n  https://b.example  \n", "utf-8")
    assert read_sites(sites) == ["https://a.example", "https://b.example"]


def test_reference_sites_file_is_valid() -> None:
    urls = read_sites(SITES_FILE)
    assert urls
    assert all(url.startswith("https://") for url in urls)


def test_build_command_uses_fresh_profile_for_chromium_browsers(tmp_path: Path) -> None:
    command = build_command("chrome", "chrome.exe", tmp_path, ["https://a.example"])
    assert command[0] == "chrome.exe"
    assert f"--user-data-dir={tmp_path}" in command
    assert command[-1] == "https://a.example"


def test_build_command_for_our_browser(tmp_path: Path) -> None:
    command = build_command("navigateur", "python", tmp_path, ["https://a.example"])
    assert command == ["python", "-m", "navigateur", "https://a.example"]


def test_cpu_percent_sums_all_processes() -> None:
    # 1 s + 2 s de CPU sur 10 s de mesure = 30 % d'un cœur.
    assert cpu_percent({1: (5.0, 6.0), 2: (0.0, 2.0)}, 10.0) == pytest.approx(30.0)


def test_cpu_percent_with_zero_duration() -> None:
    assert cpu_percent({1: (0.0, 1.0)}, 0.0) == 0.0


def test_summarize_run() -> None:
    samples = [Sample(100 * MIB, 200 * MIB, 3), Sample(300 * MIB, 400 * MIB, 5)]
    result = summarize_run(samples, cpu=12.5)
    assert result == RunResult(200.0, 300.0, 300.0, 12.5, 5)


def test_median_result_ignores_outlier_run() -> None:
    runs = [
        RunResult(100, 150, 200, 1.0, 4),
        RunResult(110, 160, 210, 2.0, 5),
        RunResult(900, 990, 999, 50.0, 9),
    ]
    assert median_result(runs) == RunResult(110, 160, 210, 2.0, 5)


def test_format_table_contains_one_row_per_browser() -> None:
    table = format_table({"chrome": RunResult(512.4, 600, 900, 3.25, 12)})
    rows = table.splitlines()
    assert len(rows) == 3
    assert rows[2] == "| chrome | 512 Mio | 600 Mio | 900 Mio | 3.2 % | 12 |"
