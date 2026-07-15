# Chenin

Turn **Génie 2000 (G2K)** gamma-spectrometry reports into structured data and an
**activity-vs-depth synthesis** for a sediment core, ready for age-depth modelling.
Built for the [EDYTEM-PTAL](https://edytem.cnrs.fr/) research group (CNRS).

Chenin does three things:

1. **Extract** — parse a raw G2K `.txt` report into six clean tables (peaks, nuclide
   activities, detection limits, …).
2. **Synthesise** — combine several reports into one table, *one row per sample*, with
   the nuclide activities and uncertainties you care about, at their depth in the core.
3. **Visualise & export** — browse everything in a web app and export to CSV, Parquet
   or SERAC.

Everything is driven by a single **roadmap** (a `.csv` or `.xlsx` spreadsheet) that
lists which reports belong to the core and at what depths. The nuclides to pull out
come from a **synthesis template**, and a sensible lab default ships with Chenin — so
in the common case the roadmap is all you write.

## Requirements

- Python ≥ 3.14
- [uv](https://docs.astral.sh/uv/) (package/environment manager)

## Install

### As a tool (for end users)

```sh
uv tool install git+https://github.com/Ezacuak/chenin.git
```

This puts a `chenin` command on your PATH. Update later with
`uv tool upgrade chenin`.

### From a clone (for development)

```sh
git clone https://github.com/Ezacuak/chenin.git
cd chenin
uv sync
```

Then prefix commands with `uv run` (e.g. `uv run chenin ...`).

## Quick start

```sh
# 1. Inspect a single report
chenin extract data/test/rapport-RGU_3cm.txt          # all sections to stdout
chenin extract data/test/rapport-RGU_3cm.txt -s s3    # just section 3
chenin extract data/test/rapport-RGU_3cm.txt -o out/  # each section to a CSV

# 2. Build a synthesis from a roadmap (uses the packaged default template)
chenin synthesis data/NOIR24-01/NOIR24-01-Roadmap.csv                  # print the table
chenin synthesis data/NOIR24-01/NOIR24-01-Roadmap.csv -o synthesis.csv # export it
chenin synthesis roadmap.csv --template my_template.csv                # custom columns

# 3. Launch the web app (recommended for day-to-day use)
chenin app
```

`chenin app` opens the Streamlit interface in your browser: load a roadmap once on the
**Roadmap** page, then browse the extracted reports and the synthesis, with a
sediment-core view and per-nuclide depth profiles.

> The bare form `chenin report.txt` still works as a shortcut for
> `chenin extract report.txt`.

## The roadmap

The roadmap is the single input you write: one row per sample, listing its report
file and its layer depths (which are *not* in the G2K reports). It is an ordinary
spreadsheet — edit it in Excel/LibreOffice and save as `.csv` or `.xlsx`. Report files
sit next to the roadmap. A cell left empty in `G2K Report` keeps a planned-but-
unmeasured layer as a depth-only row.

```csv
LSM Code, Sample Code, Depth Top, Depth Bot, DBD, G2K Report
NOIR24-01, NOI24-01-1, 0.0, 0.5, 0, NOI_S_1.txt
NOIR24-01, NOI24-01-2, 0.5, 1.0, 0, NOI_S_2.txt
NOIR24-01, NOI24-01-3, 1.0, 1.5, 0,
```

Which nuclides land in the synthesis comes from a **synthesis template**: a compact
table whose header row names the output columns and whose single method row says how
to obtain each one — gamma peaks (`NUCLIDE@energy`, `;`-separated for a weighted mean)
or an `=` formula over other columns:

```csv
PB-210,       RA-226,                                          PB-Exc,             K-40
PB-210@46.54, PB-214@295.21; PB-214@351.92; BI-214@609.31,     =[PB-210] - [RA-226], K-40@1460.82
```

The standard EDYTEM-PTAL template ships with Chenin and is applied automatically, so
most cores need only a roadmap. Pass `--template my_template.csv` (or upload one on the
Roadmap page) to override it.

See [`docs/user-guide.md`](docs/user-guide.md) for the full walkthrough, and
[`docs/synthesis.md`](docs/synthesis.md) for the complete roadmap and template schema.

## Documentation

| Document | For | Content |
|---|---|---|
| [`docs/user-guide.md`](docs/user-guide.md) | Users | End-to-end workflow: install → roadmap → reports → synthesis → export. |
| [`docs/synthesis.md`](docs/synthesis.md) | Users / power users | Full roadmap + synthesis-template schema, peaks, formulas, output columns. |
| [`docs/measurement.md`](docs/measurement.md) | Curious users / devs | The `Measurement` value object and uncertainty propagation. |
| [`CLAUDE.md`](CLAUDE.md) | Contributors | Architecture, conventions, section layout. |

## Project layout

```
src/chenin/
├── g2k_parser/     # parsing library: G2K report -> {section: DataFrame}
├── synthesis/      # roadmap/template model, report loading, synthesis builder
├── ui/             # Streamlit app (pages, components, shared state)
└── cli.py          # `chenin` command (extract / synthesis / app)
docs/               # user and reference documentation
tests/              # pytest suite
```

## Development

```sh
uv run pytest          # run the test suite
uvx ruff check src/    # lint
uv run jupyter lab     # exploration notebook
```

The G2K CSV/report conventions (French locale, section layout, key nuclides) are
documented in [`CLAUDE.md`](CLAUDE.md).
