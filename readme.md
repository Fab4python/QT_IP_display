# Matrix NetInfo

## Description

Visualiser rapidement son adresse IP exposée sur Internet, ses IP privées / serveurs DNS et sa localisation, dans une petite application de bureau au style Matrix (fond noir, texte vert).

Application réalisée en Python par prompt engineering.



## Fonctionnalités

- Adresse IP publique, fournisseur d'accès, lieu et fuseau horaire
- IP privées / serveurs DNS configurés sur la machine (opérateur et lieu pour les DNS publics)
- Petite carte de localisation, dépliable et repliable
- Rafraîchissement automatique réglable de 5 s à 5 min (30 s par défaut), avec le nombre d'appels par heure
- Compteur d'appels restants par jour (limite de 1000 appels `ipinfo.io`)

## Prérequis

- Python 3.12
- Connaissances de base en Python et dans l'utilisation d'un IDE
- Bibliothèques : `PySide6` et `requests`

## Installation

Installer les bibliothèques listées dans le fichier `requirements.txt` :

```
pip install -r requirements.txt
```

ou directement :

```
pip install PySide6 requests
```

## Exécution

```
python main.py
```

## Créer un exécutable (Windows)

```
pip install pyinstaller
pyinstaller --noconfirm --windowed --name MatrixNetInfo main.py
```

Le programme se trouve ensuite dans `dist/MatrixNetInfo/MatrixNetInfo.exe`.

## Configuration

Toutes les constantes sont dans `config.py` : couleurs, taille de la fenêtre, zoom et taille de la carte, intervalle de rafraîchissement, limite d'appels, délais d'attente.

L'application enregistre le compteur d'appels et un cache des tuiles de carte dans le dossier `~/.matrix_netinfo/`.

## Structure du projet

```
├── main.py           # point d'entrée
├── main_window.py    # interface graphique uniquement
├── worker.py         # thread qui orchestre les recherches
├── local_lookup.py   # recherche locale
├── dns_lookup.py     # définition de l'adresse DNS / IP (via Internet)
├── map_builder.py    # construction de la carte
├── config.py         # toutes les constantes
├── styles.py         # feuille de style Matrix (QSS)
├── quota.py          # compteur d'appels par jour et calcul des appels/heure
├── utils.py          # fonctions d'affichage (durées)
└── widgets.py        # widgets graphiques personnalisés (traits en pointillés)
```

## Rôle de chaque fichier

| Fichier | Rôle |
|---|---|
| `main.py` | Point d'entrée : crée l'application Qt et affiche la fenêtre. |
| `main_window.py` | La partie graphique seule, sans aucune logique réseau. Elle affiche les résultats que lui envoie le worker. |
| `worker.py` | Le lien entre les deux mondes. Il appelle les recherches dans un `QThread` pour que la fenêtre ne se fige pas, lance les opérations lentes en parallèle et envoie les résultats au fur et à mesure (IP, puis DNS, puis carte). |
| `local_lookup.py` | Tout ce que la machine sait d'elle-même, sans Internet. Il lit les serveurs DNS configurés (Windows, macOS, Linux), indique si une adresse est locale ou publique, et fait la résolution DNS inverse. |
| `dns_lookup.py` | La définition de l'adresse DNS. Avec `requests`, il identifie ton IP publique, décrit chaque serveur DNS (opérateur, lieu, coordonnées) et choisit le point à afficher sur la carte. Il ne dépend pas de Qt. |
| `map_builder.py` | Téléchargement en parallèle des seules tuiles visibles (avec cache disque), filtre vert optionnel et marqueur. Isolé car il utilise Qt pour dessiner, mais ce n'est pas de l'interface. |
| `config.py` | Couleurs, taille de fenêtre, URL, délais d'attente, zoom et taille de la carte. Pour changer le zoom, la taille de la carte ou le vert, tout se fait ici. |
| `styles.py` | Le style Qt, construit à partir des valeurs de `config.py`. |
| `quota.py` | Compteur local d'appels `ipinfo.io`, remis à zéro chaque jour et enregistré dans `~/.matrix_netinfo/quota.json`. Calcule aussi le nombre d'appels par heure selon l'intervalle de rafraîchissement. |
| `utils.py` | Mise en forme des durées (`30 s`, `5 min`, `4 h 10 min`). |
| `widgets.py` | Widgets graphiques personnalisés : le trait en pointillés (simple ou double) des séparateurs. |