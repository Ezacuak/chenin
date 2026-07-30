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

You point Chenin at a folder of reports and describe the **core layers** — which report
is which slice of sediment, and at what depth. Cores are usually cut at a constant step
with the slice number in the file name, so Chenin can generate the depths for you and
let you correct them. Which nuclides land in the table comes from a **synthesis
template**, and a sensible lab default ships with Chenin — so in the common case you
write nothing at all.

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
chenin extract data/NOIR24-01/NOI_S_1.txt          # all sections to stdout
chenin extract data/NOIR24-01/NOI_S_1.txt -s s3    # just section 3
chenin extract data/NOIR24-01/NOI_S_1.txt -o out/  # each section to a CSV

# 2. Build a synthesis from a folder of reports (uses the packaged default template)
chenin synthesis data/NOIR24-01/ --thickness 0.5                    # print the table
chenin synthesis data/NOIR24-01/ --thickness 0.5 -o synthesis.csv   # export it
chenin synthesis data/NOIR24-01/ --template my_template.csv         # custom columns

# 3. Launch the web app (recommended for day-to-day use)
chenin app
```

`chenin app` opens the Streamlit interface in your browser: upload the reports on the
**Load Data** page, describe the core layers on the **Synthesis** page, then browse the
extracted sections and the synthesis, with a sediment-core view and per-nuclide depth
profiles.

> The bare form `chenin report.txt` still works as a shortcut for
> `chenin extract report.txt`.

## Core layers

A G2K report says what a sample contains, never where it came from. The layer geometry
— depth top, depth bottom, dry bulk density — has to come from you.

Because cores are cut at a constant step and the slice number is usually written into
the file name, Chenin generates the depths from a slicing rule:

```sh
chenin synthesis data/NOIR24-01/ --start 0 --thickness 0.5
```

By default the slice number is read from the end of the file name (`NOI_S_13` → 13), so
a core with unmeasured slices keeps its true depths — if slice 12 was never counted,
slice 13 still sits at 6.0 cm instead of sliding up to fill the hole. Pass
`--sequential` to stack the reports contiguously instead. In the app the same rule
prefills the **Core layers** table, where every cell stays editable for cores that are
not regular.

## The synthesis template

Which nuclides land in the synthesis comes from a **synthesis template**: a compact
table whose header row names the output columns and whose single method row says how
to obtain each one — gamma peaks (`NUCLIDE@energy`, `;`-separated for a weighted mean)
or an `=` formula over other columns:

```csv
PB-210,       RA-226,                                          PB-Exc,             K-40
PB-210@46.54, PB-214@295.21; PB-214@351.92; BI-214@609.31,     =[PB-210] - [RA-226], K-40@1460.82
```

The standard EDYTEM-PTAL template ships with Chenin and is applied automatically. Pass
`--template my_template.csv` (or edit and download one in the app) to override it.

Each measured column yields an `Activite …`/`Incertitude …` pair, prefixed by the layer
geometry: `Echantillon`, `Profondeur`, `Epaisseur`, `DBD`.

## Documentation

Full documentation is in [`docs/`](docs/README.md). The user guide is also rendered
inside the app, under **Documentation** in the sidebar — the markdown files are the
single source for both.

| Start here | For |
|---|---|
| [Overview](docs/guide/overview.md) | What Chenin does, the workflow, the vocabulary |
| [Install & Update](docs/guide/install.md) | Getting it running |
| [Formulas](docs/guide/formulas.md) | Derived columns and uncertainty propagation |
| [Command Line](docs/guide/command-line.md) | Every subcommand and flag |
| [Troubleshooting](docs/guide/troubleshooting.md) | When something goes wrong |
| [Architecture](docs/dev/architecture.md) | Contributors: package layout and data flows |

## Project layout

```
src/chenin/
├── g2k_parser/     # parsing library: G2K report -> {section: DataFrame}
├── synthesis/      # build model, slicing rule, report loading, synthesis builder
├── ui/             # Streamlit app (pages, components, shared state)
└── cli.py          # `chenin` command (extract / synthesis / app)
docs/               # user guide (shipped + rendered in-app) and developer guide
tests/              # pytest suite
```

## Development

```sh
uv sync                     # install, including dev dependencies
uv run pytest               # run the test suite
uvx ruff check src/ tests/  # lint
uv run chenin app           # the app, against your working tree
```

See [Contributing](docs/dev/contributing.md) for the uv workflow, the documentation
house style and the conventions worth not breaking, and
[Parsing G2K reports](docs/dev/parsing-g2k.md) for the report format itself.
