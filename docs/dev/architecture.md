# Architecture

Everything lives in one installable package, `src/chenin/`, with absolute `chenin.*`
imports throughout. There are no `sys.path` tricks and no top-level scripts.

```
src/chenin/
├── __init__.py         # top-level API re-exports
├── cli.py              # argparse CLI (extract / synthesis / app); entry point for `chenin`
├── serac.py            # SERAC export: synthesis DataFrame -> serac R package input
├── g2k_parser/         # G2K report -> {section: DataFrame}
│   ├── parser.py       # G2KParser
│   ├── report.py       # Report(Mapping): sections by key or index
│   ├── columns.py      # single source of truth for all column names (ASCII)
│   ├── _sections.py    # regex patterns + extract_s*() functions
│   └── utils.py        # split_sections(), normalize_columns(), strip_accents(), format_nuclide()
├── synthesis/          # build model + synthesis builder
│   ├── config.py       # BuildConfig + Sample/Nuclide/Column specs; parse_template(); GEOMETRY_COLUMNS
│   ├── layers.py       # slice_samples()/index_from_name(): the depth rule
│   ├── default_template.csv  # packaged lab-default synthesis template (wide)
│   ├── loader.py       # load_reports(directory) -> {stem: Report}
│   ├── providers.py    # resolve_nuclide() (section-3 read) + evaluate_formula() (restricted AST)
│   ├── measurement.py  # Measurement(value, uncertainty): propagation + weighted_mean
│   └── builder.py      # SynthesisBuilder: one row per sample, depth-sorted
└── ui/                 # Streamlit app
    ├── app.py          # entry point: page nav; run via `chenin app`
    ├── state.py        # shared session state (reports, layers, nuclide library, synthesis)
    ├── app_pages/      # home, data_loader, reports, synthesis, docs/*
    └── components/     # export, dataframe_view_mode, doc_page
```

## The two data flows

### Extract

```
Report(path)
  -> G2KParser.parse(path)
  -> split_sections()                # splits on *****TITLE***** banners
  -> extract_s*_header()             # validates layout via _require(); names come from columns.py
   + extract_s*_data()
  -> dict[str, pd.DataFrame]
```

Only `s1` passes through `normalize_columns()` — its keys are dynamic metadata. `s2`–`s6`
use the ASCII constants in `columns.py` directly. Details in
[Parsing G2K reports](parsing-g2k.md).

### Synthesis

**There is no roadmap file.** The sample list comes from `slice_samples()` (CLI) or the
app's Core layers grid, and the column format from `parse_template()`, defaulting to the
packaged `default_template.csv`.

```
load_reports(dir)
  -> slice_samples()                       # depth rule
  -> BuildConfig.from_template(template, samples)
  -> SynthesisBuilder(config).build(reports)
```

Per sample the builder resolves every nuclide once via `resolve_nuclide()`, then each
column either writes its geometry field, reads its `source`, or evaluates its `formula`
over that namespace. Samples with no report become depth-only NaN rows. The result is
depth-sorted.

Two consequences of resolving the namespace from `config.nuclides`:

- A formula can only reference **measured** columns, never another formula.
- Every nuclide is resolved for every row even if no column uses it.

## The validation contract

`BuildConfig` validates in `__post_init__`, so a spec built by hand in the app is checked
exactly like one parsed from a file. It enforces:

- at least one nuclide source and at least one output column;
- every `ColumnSpec` has **exactly one** of `source`, `formula`, `geometry`;
- `source` names a known nuclide, `geometry` names a key of `GEOMETRY_COLUMNS`;
- every identifier in a `formula` resolves to a known nuclide;
- every `SampleSpec` has both depths, with `depth_bot >= depth_top`.

Operator and syntax errors inside a formula are **not** caught here — they surface at build
time, once per row.

## Column kinds

`GEOMETRY_COLUMNS` maps a geometry field to its output name:

| Field | Output column |
|---|---|
| `sample_code` | `Echantillon` |
| `depth_top` | `Profondeur` |
| `thickness` | `Epaisseur` (derived: `depth_bot - depth_top`) |
| `dbd` | `DBD` |

Geometry is a **column kind**, not a hardcoded prefix: a geometry column writes its value
unprefixed, while `source` and `formula` columns each yield an `Activite <name>` /
`Incertitude <name>` pair.

Those names are French because they feed SERAC and the lab's downstream workbooks. The UI
and the docs are English; **do not translate the data columns.**

## Measurement

`Measurement(value, uncertainty)` is a frozen dataclass carrying a 1σ uncertainty through
every operation. `+`/`-` add absolute uncertainties in quadrature, `*`/`/` add relative
ones, and `weighted_mean` does the inverse-variance combination used for multi-line
nuclides. Missing values are `(NaN, NaN)` and propagate.

Note `__truediv__` divides raw floats for the value — `_safe_div` guards only the relative
term — so division by exactly zero raises `ZeroDivisionError`. Callers that accept
user-written formulas must catch it.

## The template

The only synthesis input file is the wide template: a header row of display names and one
method row. Method cells hold `NUCLIDE@energy` (`;`-separated for a weighted mean) or an
`=` formula referencing other columns as `[Name]`.

`parse_template` slugifies display names into identifier keys (`PB-210` → `pb_210`) via
`slugify()`, and rewrites `[Name]` refs with `expand_formula_refs()`, so the formula
machinery works on plain identifiers. Both helpers are public precisely because the app and
the doc tester must preprocess formulas identically to the parser. **When writing a
template back out, turn slugs back into `[Display Name]` refs** so the file stays readable
in Excel.

A former TOML build file and a roadmap CSV both existed and were removed. Do not reintroduce
either.

## UI

Reports are uploaded on the Load Data page and held in session state; nothing is persisted.
`state.py` owns the four session keys (`reports`, `layers`, `nuclide_library`, `synthesis`)
and their accessors — pages should go through it rather than touching `st.session_state`
directly.

Page files under `app_pages/` are **scripts executed by `st.navigation`**, not imported
modules. There is no `__init__.py` anywhere under `ui/`; pages import shared code
absolutely (`from chenin.ui.components.export import export_dataframe`), which works
because `chenin.ui` and `chenin.ui.components` resolve as namespace subpackages.

Section 4 of the Synthesis page holds **five competing designs** for the column builder.
All five emit the same schema — a list of `{name, peaks|formula|geometry}` dicts —
translate it with `_schema_to_specs()`, and drive the real `SynthesisBuilder`. There is no
separate preview implementation. They are a bake-off awaiting a decision; don't invest in
polishing all five.

Documentation pages under `app_pages/docs/` are two-line stubs rendering `docs/guide/*.md`
through `ui/components/doc_page.py`. See [Contributing](contributing.md) for the house
style and how the files reach an installed wheel.
