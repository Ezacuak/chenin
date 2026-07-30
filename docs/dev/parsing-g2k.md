# Parsing G2K reports

## Section splitting

A Génie 2000 report is plain text divided by banner lines:

```
*******************************************
*****        NUCLIDE IDENTIFICATION   *****
*******************************************
```

`utils.split_sections()` matches those with a multiline regex and returns
`(titles, {title: body})`.

**Section identity is positional.** `parser.py` indexes `titles[0]` … `titles[5]`, so a
report with a missing or extra banner shifts every later section. This is a known
fragility, kept because the banner text itself varies between lab configurations.

Section 4's body is used twice — it holds two sub-tables, emitted as `s4_nucleides` and
`s4_pics`, which is why seven keys come out of six sections.

## The validate-don't-derive contract

Each section has two functions in `_sections.py`:

- `extract_sN_header(content)` — runs `_require(pattern, content, section)`, which raises
  `ValueError` if the header regex does not match, then returns the **constant column list
  from `columns.py`**. It never derives names from the file.
- `extract_sN_data(content, header)` — a `re.findall` into a DataFrame.

This split is deliberate. Deriving column names from the report would silently produce a
misaligned frame when Génie 2000's layout changes; validating instead fails loudly with
`Format de rapport inattendu pour la section sN`. If the lab's report format genuinely
changes, update the regex *and* `columns.py` together.

## columns.py

The single source of truth for every column name, imported by `_sections.py` and by
`synthesis/`. Names are stored already accent-stripped and with unit padding cleaned —
`Activite (mBq/g)`, not `Activité (mBq/g   )`.

Layout: a shared-constants block, then one block per section, each ending in an ordered
`S*_COLS` list used directly as the DataFrame `columns=` argument.

The shared constants matter most to `synthesis/providers.py`, which reads section 3 through
`NUCLIDE_COL`, `ENERGY_COL`, `ACTIVITY_COL` and `UNCERTAINTY_COL`.

## Conventions

- **`normalize_columns()`** strips accents. Applied only to `s1`, whose keys are dynamic
  metadata; `s2`–`s6` are already ASCII constants.
- **Marker columns** (`Marker`, `Marker (X)`, `Marker (*)`, …) are single-character flags
  captured as strings, then cast to `bool`/`category`.
- **`ffill`** propagates the nuclide name down grouped rows in `s3` and `s5`, where G2K
  writes it once per group.
- **`np.nan`** for missing numerics — replace empty strings before `.astype()`.
- **Long regexes** in `_sections.py` carry `# noqa: E501`.

## The Report API

`Report(path, *, name=None, parser=None)` subclasses `collections.abc.Mapping` and parses
**eagerly in `__init__`**.

```python
report = Report("NOI_S_1.txt")
report["s3"]        # by key
report[2]           # by index, in section order
report.name         # defaults to path.stem — this is the sample identifier
list(report)        # Mapping protocol: keys/items/values/in all work
```

`report.name` is load-bearing beyond display: `layers.index_from_name()` reads its trailing
digits to place the slice at its true depth.

## Nuclide names

`utils.format_nuclide()` canonicalises `210pb`, `Pb-210` and `pb 210` to `PB-210`. It
raises `ValueError` for unrecognisable names or a missing mass number. Use it anywhere user
input names a nuclide — the app's nuclide library does.

Note the peak-matching in `providers.py` compares against section 3 with **exact string
equality**, so what matters is that the template's nuclide token matches the report's
spelling, not that it is canonical.

## Adding a section

1. Add the column constants and an `S*_COLS` list to `columns.py`.
2. Add the header pattern and `extract_s*_header` / `extract_s*_data` to `_sections.py`.
3. Wire the positional index in `parser.py`.
4. Add the human description to `g2k_parser/__init__.py`'s `SECTION_DESCRIPTIONS` — the CLI
   help, the Reports page and the docs all read it from there.
5. Document the key in
   [Loading Reports](../guide/loading-reports.md) and
   [Command Line](../guide/command-line.md).

## Testing

`g2k_parser` currently has **no tests** — the suite covers `synthesis/` only. See
[known issues](known-issues.md). Test data is the NOIR24-01 core in `data/NOIR24-01/`:
13 reports with slices 12, 14 and 15 deliberately missing.
