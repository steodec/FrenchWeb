"""Diagnostic : codecs audio/vidéo et Widevine disponibles dans Qt WebEngine.

Selon la façon dont Qt WebEngine a été compilé, les codecs propriétaires (H.264, AAC)
et le module DRM Widevine (Netflix, Spotify, Disney+…) peuvent manquer. Ce script
interroge le moteur sans aucune requête réseau et affiche ce qui est réellement pris
en charge sur cette machine.

Usage : uv run python tools/check_media.py
"""

import io
import json
import sys

from PySide6.QtCore import QTimer, QUrl, qVersion
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWidgets import QApplication

# Types MIME testés : (nom affiché, type passé à MediaSource.isTypeSupported).
CODECS: list[tuple[str, str]] = [
    ("H.264 (propriétaire)", 'video/mp4; codecs="avc1.42E01E"'),
    ("HEVC / H.265 (propriétaire)", 'video/mp4; codecs="hvc1.1.6.L93.B0"'),
    ("AAC (propriétaire)", 'audio/mp4; codecs="mp4a.40.2"'),
    ("VP8", 'video/webm; codecs="vp8"'),
    ("VP9", 'video/webm; codecs="vp9"'),
    ("AV1", 'video/mp4; codecs="av01.0.05M.08"'),
    ("Opus", 'audio/webm; codecs="opus"'),
    ("Vorbis", 'audio/webm; codecs="vorbis"'),
]

TIMEOUT_MS = 15_000

# Le résultat est renvoyé à Python via le titre de la page : c'est le moyen le plus
# simple d'attendre une promesse JavaScript (requestMediaKeySystemAccess est asynchrone).
PROBE_SCRIPT = """
(async () => {
  const codecs = %s;
  const result = { codecs: {}, widevine: null };
  for (const [name, mime] of codecs) {
    result.codecs[name] = window.MediaSource ? MediaSource.isTypeSupported(mime) : false;
  }
  try {
    await navigator.requestMediaKeySystemAccess("com.widevine.alpha", [{
      initDataTypes: ["cenc", "webm"],
      // VP9 en plus de H.264 : sans codecs propriétaires, seul VP9 peut être accepté.
      videoCapabilities: [
        { contentType: 'video/webm; codecs="vp9"' },
        { contentType: 'video/mp4; codecs="avc1.42E01E"' },
      ],
    }]);
    result.widevine = "disponible";
  } catch (error) {
    result.widevine = "absent (" + error.name + ")";
  }
  document.title = "RESULT:" + JSON.stringify(result);
})();
"""


def format_report(result: dict[str, object]) -> str:
    """Met en forme le résultat renvoyé par la page."""
    lines = [f"Qt {qVersion()}", "", "Codecs (MediaSource.isTypeSupported) :"]
    codecs = result.get("codecs", {})
    assert isinstance(codecs, dict)
    for name, supported in codecs.items():
        mark = "oui" if supported else "NON"
        lines.append(f"  {name:<30} {mark}")
    lines += ["", f"Widevine (DRM) : {result.get('widevine')}"]
    return "\n".join(lines)


def main() -> int:
    """Charge une page vide locale, exécute la sonde et affiche le rapport."""
    # La console Windows n'est pas en UTF-8 par défaut : forcer l'encodage des accents.
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    app = QApplication(sys.argv)
    # Profil off-the-record : rien n'est écrit sur disque.
    profile = QWebEngineProfile()
    page = QWebEnginePage(profile)
    exit_code = 1

    def on_title_changed(title: str) -> None:
        nonlocal exit_code
        if title.startswith("RESULT:"):
            print(format_report(json.loads(title.removeprefix("RESULT:"))))
            exit_code = 0
            app.quit()

    def on_load_finished(ok: bool) -> None:
        page.runJavaScript(PROBE_SCRIPT % json.dumps(CODECS))

    def on_timeout() -> None:
        print("Échec : la sonde n'a pas répondu à temps.", file=sys.stderr)
        app.quit()

    page.titleChanged.connect(on_title_changed)
    page.loadFinished.connect(on_load_finished)
    QTimer.singleShot(TIMEOUT_MS, on_timeout)
    # Origine localhost : contexte sécurisé, requis par l'API DRM (EME). Aucun accès
    # réseau n'a lieu, le HTML est fourni directement.
    page.setHtml("<!doctype html><title>sonde</title>", QUrl("https://localhost/"))
    app.exec()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
