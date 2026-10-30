"""Point d'entrée : applique les drapeaux Chromium puis lance l'application Qt."""

import sys

from navigateur.engine.flags import apply_flags


def main() -> int:
    """Lance une fenêtre minimale (phase 0 : vérification de l'environnement)."""
    # Les drapeaux doivent être en place avant toute création de QApplication.
    apply_flags([])

    # Import tardif : Qt ne doit pas être chargé avant que l'environnement soit prêt.
    from PySide6.QtCore import QUrl
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    view = QWebEngineView()
    view.setWindowTitle("Navigateur")
    view.resize(1024, 768)
    view.load(QUrl("about:blank"))
    view.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
