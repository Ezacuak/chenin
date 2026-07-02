# Synthèse — module `synthesis`

Le module `src/synthesis/` construit une **synthèse** à partir de plusieurs rapports Génie 2000 :
un `DataFrame` avec **une ligne par rapport** et, pour chaque nucléide configuré, une colonne
d'activité et une colonne d'incertitude. La construction est pilotée par un **fichier de
configuration TOML** : le code décide *comment* lire les données, le TOML décide *quoi* extraire.

## Sommaire

- [Principe](#principe)
- [Format de configuration TOML](#format-de-configuration-toml)
  - [`title` et `metadata`](#title-et-metadata)
  - [`[nuclides.*]` — sources de mesure](#nuclides--sources-de-mesure)
  - [`[columns.*]` — colonnes affichées](#columns--colonnes-affichées)
  - [Formules](#formules)
- [Utilisation](#utilisation)
- [Colonnes de sortie](#colonnes-de-sortie)
- [Propagation d'incertitude](#propagation-dincertitude)
- [Erreurs de configuration](#erreurs-de-configuration)
- [Architecture interne](#architecture-interne)

## Principe

La synthèse se construit en deux niveaux, volontairement séparés :

1. **Les nucléides** (`[nuclides.*]`) décrivent *comment lire une activité* depuis la section 3
   d'un rapport : un nucléide est une ou plusieurs **raies gamma** (nucléide + énergie). Quand il y
   a plusieurs raies, l'activité est leur **moyenne pondérée inverse-variance**. Un nucléide est
   défini **une fois** puis réutilisable par plusieurs colonnes ou formules.

2. **Les colonnes** (`[columns.*]`) décrivent *ce qui est affiché*, dans l'ordre du fichier. Une
   colonne lit soit directement une source de nucléide (`source`), soit le résultat d'une
   **formule arithmétique** sur d'autres nucléides (`formula`).

```
rapports G2K ──▶ section 3 ──▶ [nuclides.*] ──▶ [columns.*] ──▶ DataFrame
                  (raies)      (mesures)        (affichage)
```

## Format de configuration TOML

Exemple complet (`data/NOI_S/synthesis.toml`) :

```toml
title = "Synthèse NOI_S"
version = 1.0
author = "Antonin Plard"

[metadata]
base_year = 2018             # année de l'échantillon de surface (calcul de l'âge)
taux_sedimentation = 0.2246  # cm/an (constante fournie, dérivée en externe pour l'instant)
epaisseur = 0.5              # épaisseur de tranche (cm) ; la profondeur cumule cette valeur

# --- Nucléides : sources de mesure réutilisables (toujours des raies avec énergie) --- #

[nuclides.pb210]
peaks = [{ nuclide = "PB-210", energy = 46.54 }]

[nuclides.ra226]                # estimé via ses filles à l'équilibre séculaire
peaks = [
  { nuclide = "PB-214", energy = 295.21 },
  { nuclide = "PB-214", energy = 351.92 },
  { nuclide = "BI-214", energy = 609.31 },
]

[nuclides.am241]
peaks = [{ nuclide = "AM-241", energy = 59.54 }]

[nuclides.cs137]
peaks = [{ nuclide = "CS-137", energy = 661.66 }]  # la vraie raie, pas la ligne à 32 keV

[nuclides.k40]
peaks = [{ nuclide = "K-40", energy = 1460.82 }]

# --- Colonnes : ce qui est affiché, dans l'ordre du fichier --- #

[columns.pb210]
name = "PB-210"
source = "pb210"

[columns.ra226]
name = "RA-226"
source = "ra226"

[columns.pbexc]
name = "PB-Exc"
formula = "pb210 - ra226"       # arithmétique sur les clés de nucléide

[columns.am241]
name = "AM-241"
source = "am241"

[columns.cs137]
name = "CS-137"
source = "cs137"

[columns.k40]
name = "K-40"
source = "k40"
```

### `title` et `metadata`

| Clé | Type | Rôle |
|---|---|---|
| `title` | str | Titre de la synthèse (par défaut `"Synthese"`). |
| `metadata.base_year` | float | Année de l'échantillon de surface, base du calcul d'âge. |
| `metadata.taux_sedimentation` | float | Taux de sédimentation (cm/an). |
| `metadata.epaisseur` | float | Épaisseur de tranche (cm) ; la profondeur cumule cette valeur ligne après ligne. |

Les clés top-level inconnues (`version`, `author`, …) sont **ignorées** sans erreur ; on peut s'en
servir pour documenter le fichier.

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

> **Note** : l'énergie est toujours obligatoire. Il n'existe pas de mode « lire toutes les raies du
> nucléide » — chaque raie d'identification doit être explicitement nommée.

La raie est appariée à la ligne de section 3 dont l'énergie est la **plus proche**, dans une
**tolérance de 1 keV** (`ENERGY_TOLERANCE` dans `providers.py`). Au-delà, ou si l'activité est
absente, la mesure est **manquante** (`NaN`).

### `[columns.*]` — colonnes affichées

Chaque table `[columns.<clé>]` produit une colonne de la synthèse, **dans l'ordre du fichier**. La
`<clé>` doit aussi être un identifiant valide.

```toml
[columns.pb210]
name = "PB-210"      # nom d'affichage, sert d'en-tête de colonne
source = "pb210"     # référence une clé de [nuclides.*]
```

Une colonne porte **exactement un** des deux champs suivants :

| Champ | Effet |
|---|---|
| `source` | Lit directement la mesure du nucléide de clé donnée. |
| `formula` | Évalue une expression arithmétique sur les clés de nucléide (voir ci-dessous). |

`name` est obligatoire et sert d'en-tête (`Activite <name>`, `Incertitude <name>`).

### Formules

Une colonne `calculated` utilise `formula`, une expression arithmétique qui référence les **clés de
nucléide** :

```toml
[columns.pbexc]
name = "PB-Exc"
formula = "pb210 - ra226"
```

- Opérateurs autorisés : `+`, `-`, `*`, `/` (binaires et unaires), parenthèses, et constantes
  numériques. Aucun appel de fonction, aucune autre construction (évaluation via un AST restreint).
- Les noms référencent les **clés de `[nuclides.*]`** (ici `pb210` et `ra226`), pas les noms
  d'affichage.
- L'incertitude est **propagée automatiquement** (voir plus bas).

## Utilisation

### En ligne de commande

```sh
uv run src/cli.py synthesis <config.toml> <rapport1.txt> <rapport2.txt> ...

# Exemple sur le jeu NOI_S
uv run src/cli.py synthesis data/NOI_S/synthesis.toml data/NOI_S/*.txt

# Export CSV
uv run src/cli.py synthesis data/NOI_S/synthesis.toml data/NOI_S/*.txt -o synthese.csv
```

### En Python

```python
from g2k_parser import Report
from synthesis import SynthesisBuilder

builder = SynthesisBuilder.from_toml("data/NOI_S/synthesis.toml")
reports = [Report(p) for p in ["data/NOI_S/NOI_S_1.txt", "data/NOI_S/NOI_S_2.txt"]]
df = builder.build(reports)   # une ligne par rapport, dans l'ordre fourni
```

L'ordre des lignes suit l'ordre des rapports passés à `build()`. La **profondeur** cumule
`metadata.epaisseur` à chaque ligne.

## Colonnes de sortie

Pour chaque rapport, la ligne produite contient :

| Colonne | Source |
|---|---|
| `Numero Echantillon` | Dernier entier du nom de fichier (ex. `NOI_S_13.txt` → `13`), sinon le nom. |
| `Profondeur` | Cumul de `epaisseur` (0, 0.5, 1.0, … en cm). |
| `Epaisseur` | `metadata.epaisseur`. |
| `Activite <name>` | Valeur de chaque colonne configurée. |
| `Incertitude <name>` | Incertitude (1 σ) de chaque colonne configurée. |
| `Age` | `base_year - profondeur / taux_sedimentation` (`NaN` si métadonnées manquantes). |

## Propagation d'incertitude

Les calculs passent par le type `Measurement(value, uncertainty)` (1 σ), qui propage l'incertitude
selon les règles standard :

- **Addition / soustraction** : incertitudes sommées en **quadrature**
  `σ = √(σ₁² + σ₂²)`.
- **Multiplication / division** : incertitudes **relatives** sommées en quadrature.
- **Moyenne pondérée** (plusieurs raies) : poids `1/σᵢ²`, incertitude combinée
  `√(1 / Σ(1/σᵢ²))`.

Les mesures à valeur `NaN`, à incertitude `NaN` ou à incertitude ≤ 0 sont **ignorées** dans la
moyenne pondérée ; si rien d'exploitable ne reste, le résultat est manquant.

Exemple : `PB-Exc = PB-210 − RA-226` avec `1224.40 ± 64.48` et `178.16 ± 6.20` donne
`1046.24 ± 64.77` (car `√(64.48² + 6.20²) = 64.77`).

## Erreurs de configuration

La validation se fait au chargement (`SynthesisConfig.from_toml` / `from_dict`) et lève une
`ValueError` explicite :

| Situation | Message |
|---|---|
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
src/synthesis/
├── __init__.py      # API publique : SynthesisBuilder, SynthesisConfig, NuclideSpec, Measurement, numero
├── config.py        # modèle + parsing/validation du TOML
│   ├── Peak             nuclide + energy
│   ├── NuclideSpec      key + liste de Peak
│   ├── ColumnSpec       key + name + (source | formula)
│   ├── MetadataSpec     base_year, taux_sedimentation, epaisseur
│   └── SynthesisConfig  title + metadata + nuclides + columns
├── measurement.py   # Measurement(value, uncertainty) + opérateurs + weighted_mean
├── providers.py     # lecture section 3 et évaluation des formules
│   ├── resolve_nuclide(s3, spec)        moyenne pondérée sur les raies
│   ├── evaluate_formula(formula, ns)    évaluation AST restreinte
│   └── _peak_measurement(...)           appariement raie ↔ ligne section 3 (tolérance 1 keV)
└── builder.py       # SynthesisBuilder : résout les nucléides puis assemble les lignes
```

**Flux** : `SynthesisBuilder.from_toml()` → `SynthesisConfig.from_toml()` (parse + valide) →
`build(reports)` → pour chaque rapport, `resolve_nuclide()` calcule toutes les sources une fois,
puis chaque colonne lit sa `source` ou évalue sa `formula` → `DataFrame`.

Les noms de colonnes de la section 3 (`Nom du nucleide`, `Energie (keV)`, `Activite (mBq/g)`,
`Incert. (mBq/g)`) proviennent de `g2k_parser.columns`, source unique de vérité.
