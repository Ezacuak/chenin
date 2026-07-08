# Fichier build & synthèse — module `synthesis`

Le module `src/synthesis/` construit une **synthèse** à partir de plusieurs rapports Génie 2000 :
un `DataFrame` avec **une ligne par échantillon** et, pour chaque nucléide configuré, une colonne
d'activité et une colonne d'incertitude.

Tout est piloté par un **unique fichier build TOML** qui référence à la fois :

1. la **liste ordonnée des échantillons** — chaque rapport avec sa géométrie de couche
   (`depth_top`, `depth_bot`), *données absentes des rapports G2K eux-mêmes* ;
2. le **format de synthèse** — nucléides et colonnes.

Le code décide *comment* lire les données ; le fichier build décide *quoi* extraire et *sur quels
échantillons*.

## Sommaire

- [Principe](#principe)
- [Format du fichier build TOML](#format-du-fichier-build-toml)
  - [En-tête et `base_path`](#en-tête-et-base_path)
  - [`[[samples]]` — échantillons](#samples--échantillons)
  - [`[metadata]`](#metadata)
  - [`[nuclides.*]` — sources de mesure](#nuclides--sources-de-mesure)
  - [`[columns.*]` — colonnes affichées](#columns--colonnes-affichées)
  - [Formules](#formules)
- [Utilisation](#utilisation)
- [Colonnes de sortie](#colonnes-de-sortie)
- [Propagation d'incertitude](#propagation-dincertitude)
- [Erreurs de configuration](#erreurs-de-configuration)
- [Architecture interne](#architecture-interne)

## Principe

La synthèse se construit en niveaux, volontairement séparés :

1. **Les échantillons** (`[[samples]]`) lient chaque **fichier rapport** à sa **profondeur**
   (`depth_top`/`depth_bot`, en cm). Ils sont chargés dans l'ordre du fichier.

2. **Les nucléides** (`[nuclides.*]`) décrivent *comment lire une activité* depuis la section 3
   d'un rapport : un nucléide est une ou plusieurs **raies gamma** (nucléide + énergie). Avec
   plusieurs raies, l'activité est leur **moyenne pondérée inverse-variance**. Un nucléide est
   défini **une fois** puis réutilisable par plusieurs colonnes ou formules.

3. **Les colonnes** (`[columns.*]`) décrivent *ce qui est affiché*, dans l'ordre du fichier. Une
   colonne lit soit directement une source de nucléide (`source`), soit le résultat d'une
   **formule arithmétique** sur d'autres nucléides (`formula`).

```
fichier build ──▶ [[samples]] ──▶ rapports G2K ──▶ section 3 ──▶ [nuclides.*] ──▶ [columns.*] ──▶ DataFrame
                  (+ profondeurs)                   (raies)       (mesures)        (affichage)
```

## Format du fichier build TOML

Exemple (racine `NOI_S_Builder.toml`) :

```toml
title = "Synthèse NOI_S"
description = "Rapports G2K (échantillons + profondeurs) et format de synthèse"
version = 1.0
base_path = "./data/NOI_S"

# --- Échantillons : liste ORDONNÉE, avec la géométrie de couche (cm) --- #
[[samples]]
name = "NOI_S_1.txt"
depth_top = 0.0
depth_bot = 0.5

[[samples]]
name = "NOI_S_2.txt"
depth_top = 0.5
depth_bot = 1.0

# --- Métadonnées (niveau carotte) --- #
[metadata]
base_year = 2018             # année de l'échantillon de surface (calcul de l'âge)
taux_sedimentation = 0.2246  # cm/an (constante fournie, dérivée en externe pour l'instant)

# --- Nucléides : sources de mesure réutilisables (toujours des raies avec énergie) --- #
[nuclides.pb210]
peaks = [{ nuclide = "PB-210", energy = 46.54 }]

[nuclides.ra226]                # estimé via ses filles à l'équilibre séculaire
peaks = [
  { nuclide = "PB-214", energy = 295.21 },
  { nuclide = "PB-214", energy = 351.92 },
  { nuclide = "BI-214", energy = 609.31 },
]

# --- Colonnes : ce qui est affiché, dans l'ordre du fichier --- #
[columns.pb210]
name = "PB-210"
source = "pb210"

[columns.pbexc]
name = "PB-Exc"
formula = "pb210 - ra226"       # arithmétique sur les clés de nucléide
```

### En-tête et `base_path`

| Clé | Type | Rôle |
|---|---|---|
| `title` | str | Titre de la synthèse (par défaut `"Synthese"`). |
| `base_path` | str | Dossier des rapports. Résolu **relativement au fichier build** (CLI) ou au **dossier de travail du serveur** (Streamlit). |

Les clés top-level inconnues (`version`, `author`, `description`, …) sont **ignorées** sans erreur.

### `[[samples]]` — échantillons

Tableau ordonné (`array-of-tables`). Chaque entrée lie un rapport à sa couche :

| Champ | Type | Rôle |
|---|---|---|
| `name` | str | Nom du fichier rapport, résolu sous `base_path`. |
| `depth_top` | float | Profondeur du sommet de la couche (cm). |
| `depth_bot` | float | Profondeur du fond de la couche (cm), `>= depth_top`. |

`samples` peut être vide (le fichier reste un « format seul » valide, utile pour tester une config).

### `[metadata]`

| Clé | Type | Rôle |
|---|---|---|
| `metadata.base_year` | float | Année de l'échantillon de surface, base du calcul d'âge. |
| `metadata.taux_sedimentation` | float | Taux de sédimentation (cm/an). |

> L'épaisseur n'est **plus** une métadonnée globale : elle est dérivée par échantillon
> (`depth_bot − depth_top`).

### `[nuclides.*]` — sources de mesure

Chaque table `[nuclides.<clé>]` définit une source réutilisable. La `<clé>` doit être un
**identifiant valide** (lettres, chiffres, `_` ; pas de tiret) car elle est référençable dans les
formules.

```toml
[nuclides.ra226]
peaks = [
  { nuclide = "PB-214", energy = 295.21 },
  { nuclide = "PB-214", energy = 351.92 },
  { nuclide = "BI-214", energy = 609.31 },
]
```

- `peaks` : liste **non vide** de raies. Chaque raie a obligatoirement `nuclide` (le nom tel qu'il
  apparaît en section 3, ex. `"PB-214"`) **et** `energy` (keV).
- Avec une seule raie → activité de cette raie.
- Avec plusieurs raies → **moyenne pondérée inverse-variance** (le standard scientifique pour
  combiner plusieurs lignes gamma, et ce que Génie 2000 reporte comme activité moyenne pondérée).
- Les raies peuvent appartenir à des nucléides **différents** : c'est le cas de `RA-226`, non
  mesurable directement, estimé via ses filles (`PB-214`, `BI-214`) à l'équilibre séculaire.

La raie est appariée à la ligne de section 3 dont l'énergie est la **plus proche**, dans une
**tolérance de 1 keV** (`ENERGY_TOLERANCE` dans `providers.py`). Au-delà, ou si l'activité est
absente, la mesure est **manquante** (`NaN`).

### `[columns.*]` — colonnes affichées

Chaque table `[columns.<clé>]` produit une colonne de la synthèse, **dans l'ordre du fichier**. La
`<clé>` doit aussi être un identifiant valide.

Une colonne porte **exactement un** des deux champs suivants :

| Champ | Effet |
|---|---|
| `source` | Lit directement la mesure du nucléide de clé donnée. |
| `formula` | Évalue une expression arithmétique sur les clés de nucléide (voir ci-dessous). |

`name` est obligatoire et sert d'en-tête (`Activite <name>`, `Incertitude <name>`).

### Formules

```toml
[columns.pbexc]
name = "PB-Exc"
formula = "pb210 - ra226"
```

- Opérateurs autorisés : `+`, `-`, `*`, `/` (binaires et unaires), parenthèses, et constantes
  numériques. Aucun appel de fonction, aucune autre construction (évaluation via un AST restreint).
- Les noms référencent les **clés de `[nuclides.*]`** (ici `pb210` et `ra226`), pas les noms
  d'affichage.
- L'incertitude est **propagée automatiquement** (voir [propagation](#propagation-dincertitude)).

## Utilisation

### En ligne de commande

```sh
chenin synthesis <build_file.toml>

# Exemple sur le jeu NOI_S
chenin synthesis NOI_S_Builder.toml

# Export CSV
chenin synthesis NOI_S_Builder.toml -o synthese.csv
```

Depuis un clone (au lieu de l'outil installé), préfixer par `uv run` :
`uv run chenin synthesis NOI_S_Builder.toml`.

Les rapports viennent du fichier build (`[[samples]]` + `base_path`) — inutile de les lister.

### En Python

```python
from pathlib import Path
from chenin.synthesis import BuildConfig, SynthesisBuilder, load_reports

config = BuildConfig.from_toml("NOI_S_Builder.toml")
reports = load_reports(config, Path("."))     # dict {name: Report}, lus sous base_path
df = SynthesisBuilder(config).build(reports)  # une ligne par échantillon, dans l'ordre du build
```

### Dans Streamlit

Lancer l'app avec `chenin app`. Le fichier build est importé **une seule fois** dans la barre
latérale. Les pages « Reports » et « Synthesis » consomment ensuite l'état partagé
(`state.get_build_config()`, `state.get_reports()`).

## Colonnes de sortie

Pour chaque échantillon, la ligne produite contient :

| Colonne | Source |
|---|---|
| `Profondeur` | `depth_top` de l'échantillon (cm). |
| `Epaisseur` | `depth_bot − depth_top` (cm). |
| `Activite <name>` | Valeur de chaque colonne configurée. |
| `Incertitude <name>` | Incertitude (1 σ) de chaque colonne configurée. |
| `Age` | `base_year − depth_top / taux_sedimentation` (`NaN` si métadonnées manquantes). |

## Propagation d'incertitude

Les calculs passent par le type `Measurement(value, uncertainty)` (1 σ), qui propage l'incertitude
selon les règles standard. Voir [`measurement.md`](measurement.md) pour le détail :

- **Addition / soustraction** : incertitudes sommées en **quadrature** `σ = √(σ₁² + σ₂²)`.
- **Multiplication / division** : incertitudes **relatives** sommées en quadrature.
- **Moyenne pondérée** (plusieurs raies) : poids `1/σᵢ²`, incertitude combinée `√(1 / Σ(1/σᵢ²))`.

Exemple : `PB-Exc = PB-210 − RA-226` avec `1224.40 ± 64.48` et `178.16 ± 6.20` donne
`1046.24 ± 64.77` (car `√(64.48² + 6.20²) = 64.77`).

## Erreurs de configuration

La validation se fait au chargement (`BuildConfig.from_toml` / `from_dict`) et lève une
`ValueError` explicite ; le chargement des rapports lève `FileNotFoundError` si un fichier manque.

| Situation | Message |
|---|---|
| Échantillon sans `name` | `a sample is missing its 'name'` |
| Échantillon sans `depth_top`/`depth_bot` | `sample '...' is missing 'depth_top'` |
| `depth_bot < depth_top` | `sample '...' has depth_bot (...) < depth_top (...)` |
| Rapport introuvable sous `base_path` | `rapport introuvable pour l'échantillon '...' : ...` |
| Aucune table `[nuclides.*]` | `config has no [nuclides.*] entries` |
| Aucune table `[columns.*]` | `config has no [columns.*] entries` |
| Clé non-identifiant | `nuclide key '...' is not a valid identifier` |
| `peaks` vide | `nuclide '...' needs a non-empty 'peaks'` |
| Raie sans `energy` | `nuclide '...' has a peak missing 'energy'` |
| Colonne sans `name` | `column '...' is missing a 'name'` |
| Ni / les deux de `source`/`formula` | `column '...' must have exactly one of 'source' or 'formula'` |
| `source` vers un nucléide inconnu | `column '...' references unknown nuclide '...'` |
| Opérateur interdit dans une formule | `operator ... is not allowed` |
| Nom inconnu dans une formule | `unknown nuclide '...' in formula` |

## Architecture interne

```
src/chenin/synthesis/
├── __init__.py      # API : SynthesisBuilder, BuildConfig, SampleSpec, NuclideSpec, load_reports, Measurement
├── config.py        # modèle + parsing/validation du TOML
│   ├── SampleSpec       name + depth_top + depth_bot
│   ├── Peak             nuclide + energy
│   ├── NuclideSpec      key + liste de Peak
│   ├── ColumnSpec       key + name + (source | formula)
│   ├── MetadataSpec     base_year, taux_sedimentation
│   └── BuildConfig      title + base_path + samples + metadata + nuclides + columns
├── loader.py        # load_reports(config, base_dir) : construit un Report par échantillon depuis base_path
├── measurement.py   # Measurement(value, uncertainty) + opérateurs + weighted_mean (voir measurement.md)
├── providers.py     # lecture section 3 et évaluation des formules
│   ├── resolve_nuclide(s3, spec)        moyenne pondérée sur les raies
│   ├── evaluate_formula(formula, ns)    évaluation AST restreinte
│   └── _peak_measurement(...)           appariement raie ↔ ligne section 3 (tolérance 1 keV)
└── builder.py       # SynthesisBuilder : résout les nucléides puis assemble une ligne par échantillon
```

**Flux** : `BuildConfig.from_toml()` (parse + valide) → `load_reports()` (lecture disque sous
`base_path`) → `SynthesisBuilder(config).build(reports)` → pour chaque échantillon,
`resolve_nuclide()` calcule toutes les sources une fois, puis chaque colonne lit sa `source` ou
évalue sa `formula` → `DataFrame`.

Les noms de colonnes de la section 3 (`Nom du nucleide`, `Energie (keV)`, `Activite (mBq/g)`,
`Incert. (mBq/g)`) proviennent de `g2k_parser.columns`, source unique de vérité.
