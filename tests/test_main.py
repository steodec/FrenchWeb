"""Tests du point d'entrée, avec des doublures à la place des classes Qt.

Lancer un vrai Chromium en CI serait lent et fragile : on vérifie seulement
l'ordre des opérations et la fenêtre créée.
"""

import os
from dataclasses import dataclass, field
from unittest.mock import MagicMock

import pytest
from PySide6 import QtWebEngineWidgets, QtWidgets

from navigateur import __main__ as entry
from navigateur.engine.flags import ENV_VAR


@dataclass
class FakeQt:
    """Doublures de Qt et observations faites pendant l'appel à main()."""

    app_class: MagicMock = field(default_factory=MagicMock)
    view_class: MagicMock = field(default_factory=MagicMock)
    flags_at_app_creation: list[str | None] = field(default_factory=list)


@pytest.fixture
def fake_qt(monkeypatch: pytest.MonkeyPatch) -> FakeQt:
    """Remplace QApplication et QWebEngineView par des doublures."""
    fake = FakeQt()

    def create_app(argv: list[str]) -> MagicMock:
        # Mémorise l'état des drapeaux au moment où l'application est créée.
        fake.flags_at_app_creation.append(os.environ.get(ENV_VAR))
        app = MagicMock()
        app.exec.return_value = 0
        return app

    fake.app_class.side_effect = create_app
    monkeypatch.setattr(QtWidgets, "QApplication", fake.app_class)
    monkeypatch.setattr(QtWebEngineWidgets, "QWebEngineView", fake.view_class)
    monkeypatch.delenv(ENV_VAR, raising=False)
    return fake


def test_main_sets_flags_before_creating_application(fake_qt: FakeQt) -> None:
    assert entry.main() == 0
    # La variable doit exister AVANT QApplication, sinon Chromium l'ignore.
    assert fake_qt.flags_at_app_creation == [""]


def test_main_shows_blank_page(fake_qt: FakeQt) -> None:
    entry.main()
    view = fake_qt.view_class.return_value
    view.load.assert_called_once()
    assert view.load.call_args.args[0].toString() == "about:blank"
    view.show.assert_called_once()
