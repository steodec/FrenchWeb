# FrenchWeb

[![CI](https://github.com/steodec/FrenchWeb/actions/workflows/ci.yml/badge.svg)](https://github.com/steodec/FrenchWeb/actions/workflows/ci.yml)
[![Couverture](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/steodec/FrenchWeb/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/steodec/FrenchWeb/blob/python-coverage-comment-action-data/htmlcov/index.html)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Qt WebEngine](https://img.shields.io/badge/Qt%20WebEngine-PySide6-41cd52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython-6/)
[![Plateformes](https://img.shields.io/badge/plateformes-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](#démarrer)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/mypy-strict-2a6db2)](https://mypy-lang.org/)

Navigateur web multiplateforme (Windows, macOS, Linux), open source et gratuit, qui affiche
**tous les sites correctement** en consommant **nettement moins de RAM et de CPU** que Chrome
ou Edge.

> 🚧 Projet en phase 0 (préparation). Le nom définitif n'est pas choisi.

## Principe

Le moteur est Chromium, embarqué via [Qt WebEngine](https://doc.qt.io/qt-6/qtwebengine-index.html)
(PySide6) et **jamais modifié**. Le projet apporte l'orchestration autour du moteur :

- **Bloqueur** de publicités et de trackers (moteur [`adblock`](https://github.com/brave/adblock-rust)
  de Brave, listes EasyList / EasyPrivacy) ;
- **Mise en veille des onglets** inactifs (gel puis déchargement) ;
- **Surveillance des ressources** (RAM / CPU par onglet) ;
- **Interface minimaliste** en widgets Qt natifs.

Engagements : sandbox Chromium toujours active, aucune télémétrie, aucune donnée persistante en V1.

## Démarrer

Prérequis : [uv](https://docs.astral.sh/uv/) (il installe lui-même Python si besoin).

```bash
uv sync                       # installer les dépendances
uv run python -m navigateur   # lancer le navigateur
```

## Développement

```bash
uv run pytest                                  # tests + couverture (minimum 80 %)
uv run ruff check . && uv run ruff format .    # lint + format
uv run mypy src tests                          # typage
```

Ces vérifications sont exécutées automatiquement par la CI sur Windows, macOS et Linux, pour
chaque push sur `main` et chaque pull request.

## Mesures

La consommation RAM/CPU est comparée à Chrome et Edge avec un protocole fixe (jeu de sites,
profil vierge, médiane de plusieurs passes) :

```bash
uv run python benchmarks/run_benchmark.py
```

Détails du protocole et des indicateurs : [benchmarks/README.md](benchmarks/README.md).

## Feuille de route

0. Préparation : environnement, vérification codecs/Widevine, licence, protocole de mesure
1. Navigateur minimal : onglets, barre d'adresse, navigation, recherche, téléchargements
2. Économies automatiques : bloqueur + liste blanche, veille des onglets
3. Contrôle des ressources : moniteur RAM/CPU, seuils, panneau, réglages
4. Publication : installeurs 3 OS, mesures publiées → v0.1

## Licence

À définir (phase 0).
