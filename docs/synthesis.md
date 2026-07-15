# Roadmap & synthèse — module `synthesis`

Le module `src/chenin/synthesis/` construit une **synthèse** à partir de plusieurs rapports
Génie 2000 : un `DataFrame` avec **une ligne par échantillon** et, pour chaque colonne configurée,
une valeur d'activité et une valeur d'incertitude.

Deux entrées, toutes deux des tableurs ordinaires (`.csv`/`.xlsx`) :

1. la **roadmap** — la **liste ordonnée des échantillons** : chaque rapport avec sa géométrie de
   couche (`Depth Top`, `Depth Bot`) et sa densité (`DBD`), *données absentes des rapports G2K
   eux-mêmes* ;
2. le **template de synthèse** — le **format** : quelles colonnes de sortie et comment les obtenir.
   Un template par défaut est livré avec Chenin ; dans le cas courant, seule la roadmap est écrite.

Le code décide *comment* lire les données ; la roadmap et le template décident *quoi* extraire et
*sur quels échantillons*.

## Sommaire

- [Principe](#principe)
- [La roadmap](#la-roadmap)
- [Le template de synthèse](#le-template-de-synthèse)
  - [Raies gamma](#raies-gamma)
  - [Formules](#formules)
- [Utilisation](#utilisation)
- [Colonnes de sortie](#colonnes-de-sortie)
- [Propagation d'incertitude](#propagation-dincertitude)
- [Erreurs de configuration](#erreurs-de-configuration)
- [Architecture interne](#architecture-interne)

## Principe

```
roadmap ─────▶ échantillons ──▶ rapports G2K ──▶ section 3 ─┐
(+ profondeurs, DBD)            (raies)                     ├─▶ DataFrame
template ────▶ colonnes ────────────────────────────────────┘
(raies | formule)
```

1. **La roadmap** lie chaque **fichier rapport** à sa **profondeur** (`Depth Top`/`Depth Bot`, en
   cm). Les échantillons sont chargés dans l'ordre du fichier. Une ligne sans rapport reste une
   **ligne « profondeur seule »** (activités `NaN`).

2. **Le template** décrit chaque **colonne de sortie**. Une colonne est soit une **mesure directe**
   (une ou plusieurs raies gamma lues en section 3), soit une **formule arithmétique** sur d'autres
   colonnes. Avec plusieurs raies, l'activité est leur **moyenne pondérée inverse-variance**.

## La roadmap

Un CSV (séparateur `,`) ou un classeur Excel. Les rapports sont cherchés **à côté de la roadmap**
(ou dans le dossier indiqué à l'app). Colonnes attendues (repérées par leur nom, l'ordre et les
espaces autour importent peu) :

```csv
LSM Code, Sample Code, Depth Top, Depth Bot, DBD, G2K Report
NOIR24-01, NOI24-01-1, 0.0, 0.5, 0, NOI_S_1.txt
NOIR24-01, NOI24-01-2, 0.5, 1.0, 0, NOI_S_2.txt
NOIR24-01, NOI24-01-3, 1.0, 1.5, 0,
```

| Colonne | Rôle |
|---|---|
| `LSM Code` | Identifiant de la carotte (devient le titre de la synthèse). |
| `Sample Code` | Identifiant lisible de l'échantillon (colonne `Echantillon` en sortie). |
| `Depth Top` | Profondeur du sommet de la couche (cm). |
| `Depth Bot` | Profondeur du fond de la couche (cm), `>= Depth Top`. |
| `DBD` | Densité sèche apparente (*dry bulk density*), reportée telle quelle. |
| `G2K Report` | Nom du fichier rapport. **Vide** → couche planifiée mais non mesurée (ligne profondeur seule). |

## Le template de synthèse

Un CSV **large** : la première ligne donne les **noms des colonnes** de sortie, la seconde ligne
donne la **méthode** de chaque colonne.

```csv
PB-210,       RA-226,                                       PB-Exc,               K-40
PB-210@46.54, PB-214@295.21; PB-214@351.92; BI-214@609.31,  =[PB-210] - [RA-226],  K-40@1460.82
```

Le template par défaut (`PB-210, RA-226, PB-Exc, AM-241, CS-137, K-40`) est empaqueté dans
`chenin/synthesis/default_template.csv` et appliqué automatiquement. En fournir un remplace le
défaut (`--template` en CLI, ou l'upload « template personnalisé » sur la page Roadmap).

### Raies gamma

Une cellule sans `=` décrit une **mesure directe** sous forme de raies :

- `PB-210@46.54` — une seule raie (`NUCLEIDE@énergie`, énergie en keV).
- `PB-214@295.21; PB-214@351.92; BI-214@609.31` — plusieurs raies séparées par `;` → **moyenne
  pondérée inverse-variance** (standard pour combiner plusieurs lignes gamma).
- Les raies peuvent appartenir à des nucléides **différents** : c'est le cas de `RA-226`, non
  mesurable directement, estimé via ses filles (`PB-214`, `BI-214`) à l'équilibre séculaire.

Chaque raie est appariée à la ligne de section 3 dont l'énergie est la **plus proche**, dans une
**tolérance de 1 keV** (`ENERGY_TOLERANCE` dans `providers.py`). Au-delà, ou si l'activité est
absente, la mesure est **manquante** (`NaN`).

### Formules

Une cellule commençant par `=` est une **formule** sur d'autres colonnes, référencées par leur nom
entre crochets :

```
=[PB-210] - [RA-226]
```

- Opérateurs autorisés : `+`, `-`, `*`, `/` (binaires et unaires), parenthèses, et constantes
  numériques. Aucun appel de fonction (évaluation par un AST restreint).
- Les crochets `[...]` autorisent tirets et espaces dans les noms de colonnes ; en interne, chaque
  nom est réduit à une clé identifiant (`PB-210` → `pb_210`).
- Une formule référence des colonnes **de type mesure** (raies) ; référencer une autre formule
  n'est pas supporté.
- L'incertitude est **propagée automatiquement** (voir [propagation](#propagation-dincertitude)).

## Utilisation

### En ligne de commande

```sh
chenin synthesis <roadmap.csv>                       # template par défaut, table à l'écran
chenin synthesis <roadmap.csv> -o synthese.csv       # export CSV
chenin synthesis <roadmap.csv> --template <t.csv>    # colonnes personnalisées

# Exemple sur le jeu NOIR24-01
chenin synthesis data/NOIR24-01/NOIR24-01-Roadmap.csv
```

Depuis un clone (au lieu de l'outil installé), préfixer par `uv run`.

### En Python

```python
from pathlib import Path
from chenin.synthesis import BuildConfig, SynthesisBuilder, load_reports

config = BuildConfig.from_roadmap("data/NOIR24-01/NOIR24-01-Roadmap.csv")  # template optionnel en 2e arg
reports = load_reports(config, Path("data/NOIR24-01"))  # dict {name: Report}
df = SynthesisBuilder(config).build(reports)             # une ligne par échantillon, dans l'ordre
```

### Dans Streamlit

Lancer l'app avec `chenin app`. La roadmap est chargée **une seule fois** sur la page « Roadmap »
(avec le dossier des rapports). Les pages « Reports » et « Synthesis » consomment ensuite l'état
partagé (`state.get_build_config()`, `state.get_reports()`).

## Colonnes de sortie

Pour chaque échantillon, la ligne produite contient :

| Colonne | Source |
|---|---|
| `Echantillon` | `Sample Code` de la roadmap. |
| `Profondeur` | `Depth Top` de l'échantillon (cm). |
| `Epaisseur` | `Depth Bot − Depth Top` (cm). |
| `DBD` | Densité sèche apparente de la roadmap. |
| `Activite <name>` | Valeur de chaque colonne du template (`NaN` si pas de rapport). |
| `Incertitude <name>` | Incertitude (1 σ) de chaque colonne (`NaN` si pas de rapport). |

## Propagation d'incertitude

Les calculs passent par le type `Measurement(value, uncertainty)` (1 σ), qui propage l'incertitude
selon les règles standard. Voir [`measurement.md`](measurement.md) pour le détail :

- **Addition / soustraction** : incertitudes sommées en **quadrature** `σ = √(σ₁² + σ₂²)`.
- **Multiplication / division** : incertitudes **relatives** sommées en quadrature.
- **Moyenne pondérée** (plusieurs raies) : poids `1/σᵢ²`, incertitude combinée `√(1 / Σ(1/σᵢ²))`.

Exemple : `PB-Exc = PB-210 − RA-226` avec `1224.40 ± 64.48` et `178.16 ± 6.20` donne
`1046.24 ± 64.77` (car `√(64.48² + 6.20²) = 64.77`).

## Erreurs de configuration

La validation se fait au chargement (`BuildConfig.from_roadmap` / `from_dict`) et lève une
`ValueError` explicite ; le chargement des rapports lève `FileNotFoundError` si un fichier nommé
manque.

| Situation | Message |
|---|---|
| Colonne roadmap manquante | `roadmap is missing column(s): ...` |
| Échantillon sans `Depth Top`/`Depth Bot` | `a sample is missing 'depth_top'` |
| `Depth Bot < Depth Top` | `sample at depth ... has depth_bot (...) < depth_top (...)` |
| Rapport nommé introuvable | `report not found for sample '...': ...` |
| Template sans ligne méthode | `synthesis template has no method row` |
| Colonne de template sans méthode | `column '...' has no method` |
| Raie mal formée | `column '...': peak '...' must be NUCLIDE@energy` |
| Énergie invalide | `column '...': peak '...' has an invalid energy` |
| Template sans colonne mesurée | `synthesis template has no measured (peak) columns` |

## Architecture interne

```
src/chenin/synthesis/
├── __init__.py            # API : SynthesisBuilder, BuildConfig, SampleSpec, NuclideSpec, load_reports, Measurement
├── config.py              # modèle + parsing/validation (roadmap CSV/Excel + template large)
│   ├── SampleSpec            name? + depth_top + depth_bot + sample_code? + dbd?
│   ├── Peak                  nuclide + energy
│   ├── NuclideSpec           key + liste de Peak
│   ├── ColumnSpec            key + name + (source | formula)
│   ├── MetadataSpec          base_year?, taux_sedimentation?, coring_yr?
│   ├── BuildConfig           title + samples + metadata + nuclides + columns
│   ├── parse_roadmap()       CSV/Excel -> échantillons + id de carotte
│   └── parse_template()      CSV large -> nucléides + colonnes
├── default_template.csv   # template EDYTEM-PTAL par défaut
├── loader.py              # load_reports(config, base_dir) : un Report par échantillon mesuré
├── measurement.py         # Measurement(value, uncertainty) + opérateurs + weighted_mean
├── providers.py           # lecture section 3 et évaluation des formules
│   ├── resolve_nuclide(s3, spec)        moyenne pondérée sur les raies
│   ├── evaluate_formula(formula, ns)    évaluation AST restreinte
│   └── _peak_measurement(...)           appariement raie ↔ ligne section 3 (tolérance 1 keV)
└── builder.py             # SynthesisBuilder : résout les nucléides puis assemble une ligne par échantillon
```

**Flux** : `BuildConfig.from_roadmap()` (parse roadmap + template → `from_dict`, valide) →
`load_reports()` (lecture disque à côté de la roadmap) → `SynthesisBuilder(config).build(reports)` →
pour chaque échantillon, `resolve_nuclide()` calcule toutes les sources une fois, puis chaque colonne
lit sa `source` ou évalue sa `formula` → `DataFrame`.

Les noms de colonnes de la section 3 (`Nom du nucleide`, `Energie (keV)`, `Activite (mBq/g)`,
`Incert. (mBq/g)`) proviennent de `g2k_parser.columns`, source unique de vérité.
