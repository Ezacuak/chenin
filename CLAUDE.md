# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Parses **Génie 2000 (G2K)** gamma spectrometry reports (plain `.txt`) into pandas DataFrames and CSV exports. The tool is used by EDYTEM-PTAL researchers.

## Commands

```sh
# Install dependencies
uv sync

# Run the CLI (print all sections)
uv run src/poc.py data/rapport-RGTh_3cm.txt

# Export all sections to CSV
uv run src/poc.py data/rapport-RGTh_3cm.txt -o out/

# Display a single section
uv run src/poc.py data/rapport-RGTh_3cm.txt -s s3

# Launch Jupyter for interactive exploration
uv run jupyter lab
```

No test suite or linter is configured yet. `ruff` cache is present — run `uvx ruff check src/` to lint.

## Architecture

All extraction logic lives in [src/poc.py](src/poc.py). There is no package structure; the single file is both the library and the CLI entry point.

**Data flow**: raw `.txt` report → `split_sections()` → per-section `extract_*()` → dict of DataFrames → CSV or stdout.

### Section parsing

`split_sections(content)` splits the report on `*****TITLE*****` banner lines using `section_header_pattern`. Returns a dict keyed by section title string (French). Sections are then accessed by positional index (e.g. `titles[0]` = s1, `titles[1]` = s2, …).

### Per-section extractors

Each section has two functions:

| Function | Role |
|---|---|
| `extract_header_sN(content)` | Parses the column-header block via regex; returns a list of column name strings |
| `extract_data_sN(content, header)` | `re.findall` on data rows → `pd.DataFrame(matches, columns=header)` → type casts |

**s1** is different: no header function — it's a flat key/value block parsed with `s1_kv_pattern` into a single-row DataFrame.

**s4** has two sub-tables: `s4_nucleides` (one row per nuclide) and `s4_pics` (one row per peak), each with their own header/data function pair.

### Column naming convention

Column names are assembled from multi-line header text in the report, e.g. `"Energie (keV)"`, `"Activité (mBq/g   )"`. The trailing whitespace in units like `(mBq/g   )` is intentional — it mirrors the raw report format.

Marker columns (single-character flags in the data) are named `"Marker (X)"`, `"Marker (*)"`, etc., and cast to `bool` or `category`.

### Type casting

After building the DataFrame from string matches, each extractor applies explicit `.astype()` calls. Missing values use `np.nan` (replacing empty strings before casting). Forward-fill (`ffill`) propagates the nuclide name down grouped rows in s3 and s5.

### `parse_report(path)`

Top-level function that calls all extractors in order and returns a dict:
`{"s1": df, "s2": df, "s3": df, "s4_nucleides": df, "s4_pics": df, "s5": df, "s6": df}`

## Data

Sample reports are in [data/](data/) (`.txt` format). Pre-exported CSVs are in [out/](out/). The `.ipynb` notebook at [src/poc.ipynb](src/poc.ipynb) is used for interactive exploration.
