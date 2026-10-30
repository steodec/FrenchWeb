"""Construction de la variable QTWEBENGINE_CHROMIUM_FLAGS.

Qt WebEngine lit cette variable d'environnement une seule fois, au démarrage du moteur :
elle doit donc être définie AVANT la création de QApplication, sinon elle est ignorée
silencieusement. Ce module ne dépend pas de Qt pour rester testable.
"""

import os
from collections.abc import Iterable, MutableMapping

ENV_VAR = "QTWEBENGINE_CHROMIUM_FLAGS"

# Drapeaux qui affaiblissent la sandbox Chromium : interdits sans exception (règle n° 1).
FORBIDDEN_FLAGS = frozenset({"--no-sandbox", "--disable-gpu-sandbox"})


def build_flags(flags: Iterable[str]) -> str:
    """Assemble les drapeaux en une chaîne, en refusant ceux qui désactivent la sandbox."""
    flag_list = list(flags)
    for flag in flag_list:
        name = flag.split("=", 1)[0]
        if name in FORBIDDEN_FLAGS:
            raise ValueError(f"Drapeau interdit (désactive la sandbox) : {flag}")
    return " ".join(flag_list)


def apply_flags(flags: Iterable[str], environ: MutableMapping[str, str] | None = None) -> None:
    """Ajoute les drapeaux à l'environnement, sans écraser ceux déjà présents."""
    env = os.environ if environ is None else environ
    existing = env.get(ENV_VAR, "").split()
    # Les drapeaux existants passent aussi par build_flags pour être vérifiés.
    env[ENV_VAR] = build_flags([*existing, *flags])
