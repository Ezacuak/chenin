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

Everything is driven by a single **build file** (a `.toml`) that says which reports
belong to the core, at what depths, and which nuclides to pull out.

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

# 2. Build a synthesis from a build file
chenin synthesis NOI_S_Builder.toml                   # print the table
chenin synthesis NOI_S_Builder.toml -o synthesis.csv  # export it

# 3. Launch the web app (recommended for day-to-day use)
chenin app
```

`chenin app` opens the Streamlit interface in your browser: import a build file once
in the sidebar, then browse the extracted reports and the synthesis, with a
sediment-core view and per-nuclide depth profiles.

> The bare form `chenin report.txt` still works as a shortcut for
> `chenin extract report.txt`.

## The build file

A build file is the single input that drives Chenin. It lists the core's samples
(report file + layer depths, which are *not* in the G2K reports) and the synthesis
format (which nuclides, which columns):

```toml
title = "NOI_S core"
base_path = "./data/NOI_S"      # where the report files live

[[samples]]                     # one entry per report, in core order (depths in cm)
name = "NOI_S_1.txt"
depth_top = 0.0
depth_bot = 0.5

[[samples]]
name = "NOI_S_2.txt"
depth_top = 0.5
depth_bot = 1.0

[nuclides.pb210]                # a measurement source: one or more gamma peaks
peaks = [{ nuclide = "PB-210", energy = 46.54 }]

[nuclides.ra226]                # several peaks → inverse-variance weighted mean
peaks = [
  { nuclide = "PB-214", energy = 295.21 },
  { nuclide = "BI-214", energy = 609.31 },
]

[columns.pb210]                 # a synthesis column reading a nuclide directly
name = "PB-210"
source = "pb210"

[columns.pbexc]                 # or computed from a formula over nuclide keys
name = "PB-Exc"
formula = "pb210 - ra226"
```

You don't have to write TOML by hand — the **Build file** page in the web app is a
form-based editor that validates as you type and exports a ready-to-use build file.

See [`docs/user-guide.md`](docs/user-guide.md) for the full walkthrough, and
[`docs/synthesis.md`](docs/synthesis.md) for the complete build-file schema.

## Documentation

| Document | For | Content |
|---|---|---|
| [`docs/user-guide.md`](docs/user-guide.md) | Users | End-to-end workflow: install → build file → reports → synthesis → export. |
| [`docs/synthesis.md`](docs/synthesis.md) | Users / power users | Full build-file schema, nuclides, columns, formulas, output columns. |
| [`docs/measurement.md`](docs/measurement.md) | Curious users / devs | The `Measurement` value object and uncertainty propagation. |
| [`CLAUDE.md`](CLAUDE.md) | Contributors | Architecture, conventions, section layout. |

## Project layout

```
src/chenin/
├── g2k_parser/     # parsing library: G2K report -> {section: DataFrame}
├── synthesis/      # build-file model, report loading, synthesis builder
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
