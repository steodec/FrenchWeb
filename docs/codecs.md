# Codecs et Widevine

Vérification faite en phase 0 avec `tools/check_media.py`, qui interroge le moteur sans
aucune requête réseau :

```bash
uv run python tools/check_media.py
```

## Résultats (PySide6 6.12.0 de PyPI, Windows 11, 2026-10-30)

| Format                 | Pris en charge | Remarque                                        |
| ---------------------- | -------------- | ----------------------------------------------- |
| H.264                  | **non**        | codec propriétaire, absent des wheels PyPI      |
| HEVC / H.265           | **non**        | codec propriétaire                              |
| AAC                    | **non**        | codec propriétaire                              |
| VP8, VP9, AV1          | oui            |                                                 |
| Opus, Vorbis           | oui            |                                                 |
| Widevine (DRM)         | oui\*          | \*seulement si Chrome est installé (voir plus bas) |

À refaire sur macOS et Linux, et à chaque montée de version de PySide6.

## Conséquences

**Codecs propriétaires absents.** Les binaires Qt officiels (donc les wheels PySide6) sont
compilés sans H.264 ni AAC, pour des raisons de brevets. Les sites qui proposent aussi du
VP9 ou de l'AV1 (YouTube, la plupart des grandes plateformes) fonctionnent ; ceux qui ne
servent que du MP4 H.264/AAC (certains lecteurs vidéo de sites d'actualité, Twitch, des
vidéos intégrées anciennes) n'afficheront pas leurs vidéos. C'est en contradiction avec
l'objectif « tous les sites s'affichent correctement » : décision à prendre avant la phase 1.

Pistes :

1. Compiler Qt WebEngine avec `-webengine-proprietary-codecs` et l'embarquer dans nos
   installeurs. Compilation longue (plusieurs heures), et distribuer H.264/AAC pose une
   question de licences de brevets à étudier.
2. Sous Linux, utiliser le Qt WebEngine de la distribution quand il est compilé avec ces
   codecs (par exemple Arch Linux), au lieu de celui fourni par PySide6.
3. Accepter la limite en V1 et l'indiquer clairement dans le README.

**Widevine dépend de Chrome.** Qt WebEngine ne fournit pas le module Widevine : sous
Windows il réutilise automatiquement celui de l'installation de Chrome. Sans Chrome, les
services protégés par DRM (Netflix, Spotify Web, Disney+, Prime Video…) ne fonctionneront
pas. Le drapeau documenté `--widevine-path=<chemin>` permet d'indiquer un autre module.
Seul le niveau de sécurité L3 est disponible : certains services limitent alors la
résolution (souvent 720p ou moins).

## Piège rencontré

Une configuration Widevine qui ne demande que de la vidéo H.264 est refusée
(`NotSupportedError`) même quand Widevine est présent, parce que le codec manque. La sonde
propose donc VP9 et H.264.
