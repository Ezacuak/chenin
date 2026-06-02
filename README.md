# PTAL Analyse

Outil pour la plateforme PTAL d'EDYTEM. Extrait et structure les données issues des rapports de spectrométrie gamma générés par **Génie 2000 (G2K)**.

Les rapports G2K sont des fichiers texte structurés en sections. Cet outil les parse par regex pour produire des données exploitables (CSV, DataFrames pandas).

## Fonctionnement

Le rapport G2K est découpé en sections délimitées par des bandeaux `*****` :

| Section | Contenu |
|---------|---------|
| S1 | Métadonnées du rapport (échantillon, dates, géométrie) |
| S2 | Analyse des pics |
| S3 | Identification des nucléides |
| S4 | Identification avec correction d'interférence |
| S5 | Limites de détection |
| S6 | Limites de détection ISO 11929 |

Le notebook [src/poc.ipynb](src/poc.ipynb) est le point d'entrée principal. Il illustre l'extraction section par section et exporte les résultats (ex. S6 → CSV).

## Installation

Ce projet utilise [uv](https://docs.astral.sh/uv/) pour la gestion de l'environnement.

### Prérequis

- Python >= 3.14
- `uv` installé ([guide Linux/macOS](https://docs.astral.sh/uv/getting-started/installation/) / [guide Windows](https://docs.astral.sh/uv/getting-started/installation/#windows))

### Mise en place

```bash
# Cloner le dépôt
git clone <url-du-repo>
cd ptal-analyse

# Créer l'environnement et installer les dépendances
uv sync
```

### Lancer le notebook

```bash
# Avec Jupyter Lab
uv run jupyter lab

# Avec Jupyter Notebook classique
uv run jupyter notebook
```

Ouvrir ensuite [src/poc.ipynb](src/poc.ipynb).

## Dépendances

| Paquet | Rôle |
|--------|------|
| `pandas` | Manipulation des données tabulaires |
| `matplotlib` | Visualisation |
| `ipykernel` | Exécution dans Jupyter |

## Structure du projet

```
ptal-analyse/
├── data/               # Rapports G2K (.txt) et sorties parsées (.csv)
├── src/
│   ├── poc.ipynb       # Notebook de POC — extraction par section
│   └── main.py         # Point d'entrée CLI (en développement)
├── pyproject.toml
└── README.md
```
