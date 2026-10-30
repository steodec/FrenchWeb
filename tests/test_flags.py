"""Tests de la construction des drapeaux Chromium (sans lancer Qt)."""

import pytest

from navigateur.engine.flags import ENV_VAR, apply_flags, build_flags


def test_build_flags_joins_with_spaces() -> None:
    assert build_flags(["--a", "--b=1"]) == "--a --b=1"


@pytest.mark.parametrize("flag", ["--no-sandbox", "--disable-gpu-sandbox=1"])
def test_build_flags_rejects_sandbox_flags(flag: str) -> None:
    with pytest.raises(ValueError):
        build_flags([flag])


def test_apply_flags_keeps_existing_flags() -> None:
    environ = {ENV_VAR: "--existing"}
    apply_flags(["--new"], environ)
    assert environ[ENV_VAR] == "--existing --new"


def test_apply_flags_rejects_forbidden_existing_flag() -> None:
    with pytest.raises(ValueError):
        apply_flags([], {ENV_VAR: "--no-sandbox"})
