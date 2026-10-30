# Protocole de mesure RAM / CPU

La faible consommation est la raison d'être du projet : toute modification qui peut
l'affecter est mesurée avant/après avec ce protocole, et les résultats sont indiqués dans
la description du commit ou de la PR.

```bash
uv run python benchmarks/run_benchmark.py                          # Chrome et Edge, 3 passes
uv run python benchmarks/run_benchmark.py --browsers navigateur,chrome,edge
uv run python benchmarks/run_benchmark.py --json resultats.json   # garder les chiffres
```

## Déroulé d'une passe

1. Le navigateur est lancé avec un **profil temporaire vierge** (`--user-data-dir`), sans
   écran de premier lancement, avec les sites de [`sites.txt`](sites.txt) ouverts chacun dans
   un onglet.
2. Attente du chargement : `--load-time`, 45 s par défaut.
3. Mesure pendant `--measure-time` (60 s), avec un relevé toutes les `--interval` (2 s) de
   **tout l'arbre de processus** : processus principal, processus de rendu, GPU et
   utilitaires Chromium.
4. Fermeture du navigateur et de tous ses processus, suppression du profil.

Chaque navigateur fait `--runs` passes (3 par défaut) ; on garde la **médiane** de chaque
indicateur, moins sensible qu'une moyenne à une passe perturbée.

## Indicateurs

| Indicateur      | Signification                                                                 |
| --------------- | ----------------------------------------------------------------------------- |
| RAM moy. (USS)  | Mémoire **propre** moyenne de l'arbre : celle qui serait libérée en le fermant. Indicateur principal. |
| RAM pic (USS)   | Plus haute valeur relevée pendant la mesure.                                  |
| RSS moy.        | Mémoire résidente : compte plusieurs fois la mémoire partagée entre processus, donnée à titre indicatif. |
| CPU moy.        | Temps CPU consommé pendant la mesure ÷ durée, en % **d'un cœur** (peut dépasser 100 %). |
| Processus       | Nombre maximal de processus dans l'arbre.                                     |

## Bonnes pratiques

- Fermer les autres applications lourdes, brancher le portable sur secteur.
- Comparer uniquement des mesures faites sur la même machine, le même jour, avec le même
  `sites.txt` : le contenu des sites change dans le temps.
- Indiquer la machine (OS, CPU, RAM) avec les résultats.

## Limites connues

- Tant que la phase 1 n'est pas terminée, `navigateur` n'ouvre qu'une page vide et ignore
  les URL : sa mesure n'est pas encore comparable à celle de Chrome ou Edge.
- Les sites affichent parfois un bandeau de cookies ou une vérification anti-robot : c'est
  le cas pour tous les navigateurs, donc la comparaison reste équitable.
- Le benchmark fait des requêtes réseau vers les sites de test : c'est un outil de
  développement, il n'est pas concerné par la règle « aucune requête du navigateur ».
