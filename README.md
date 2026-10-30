# FrenchWeb

Navigateur web multiplateforme (Windows, macOS, Linux), open source et gratuit, qui affiche
tous les sites correctement en consommant nettement moins de RAM et de CPU que Chrome ou Edge.

Le moteur est Chromium, embarqué via Qt WebEngine (PySide6) et jamais modifié. Le projet apporte
l'orchestration autour : bloqueur de publicités et trackers, mise en veille des onglets,
surveillance des ressources, interface minimaliste.

> Projet en phase 0 (préparation). Le nom définitif n'est pas choisi.

## Démarrer

```bash
uv sync                       # installer les dépendances
uv run python -m navigateur   # lancer le navigateur
uv run pytest                 # lancer les tests
```
