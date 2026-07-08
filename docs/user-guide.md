# Chenin — user guide

This guide walks you through Chenin end to end: from a folder of raw Génie 2000
reports to an activity-vs-depth synthesis you can export for age-depth modelling.
No prior programming experience is required.

- [Concepts](#concepts)
- [Install](#install)
- [Launch the app](#launch-the-app)
- [Step 1 — Create a build file](#step-1--create-a-build-file)
- [Step 2 — Load the build file](#step-2--load-the-build-file)
- [Step 3 — Inspect the reports](#step-3--inspect-the-reports)
- [Step 4 — Build and read the synthesis](#step-4--build-and-read-the-synthesis)
- [Step 5 — Export](#step-5--export)
- [Doing it from the command line](#doing-it-from-the-command-line)
- [Troubleshooting](#troubleshooting)

## Concepts

Four words cover everything Chenin does.

- **Report** — one raw Génie 2000 `.txt` file, the output for a single measured
  sample. Chenin parses it into six tables (sections `s1`–`s6`): metadata, peaks,
  nuclide activities, interference-corrected activities, and two detection-limit
  tables.
- **Sample** — a report *plus its depth in the core*. The report tells you the
  activities; it does **not** know where in the core the sample came from — that's
  field data you provide.
- **Build file** — a single `.toml` file that ties it all together: the ordered list
  of samples (report + depths) and the synthesis format (which nuclides, which
  columns). One build file describes one core.
- **Synthesis** — the result: a table with **one row per sample**, each nuclide's
  activity and uncertainty, and the depth. This is what you export.

The flow is always the same:

```
reports (.txt)  +  depths        →  build file (.toml)  →  synthesis (table)
                (you provide)         (one per core)         (one row per sample)
```

## Install

You need [uv](https://docs.astral.sh/uv/), a small tool that manages Python for you.

**Windows** — open PowerShell and run:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux** — open a terminal and run:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install Chenin itself:

```sh
uv tool install git+https://github.com/Ezacuak/chenin.git
```

You now have a `chenin` command. Check it with `chenin --help`.

## Launch the app

```sh
chenin app
```

Your browser opens on the Chenin interface. The top bar has four pages —
**Home**, **Build file**, **Reports**, **Synthesis** — and the sidebar (left) is where
you load your build file. You'll work left to right through the pages.

> Prefer the command line? Skip to
> [Doing it from the command line](#doing-it-from-the-command-line). The app and the
> CLI use the exact same build file and produce the exact same synthesis.

## Step 1 — Create a build file

You have two options.

### Option A — the Build file editor (recommended)

Open the **Build file** page. It's a form, no TOML to write:

1. **General** — give the core a *Title* and set the *Reports folder* (`base_path`):
   the folder that contains your `.txt` reports. This path is relative to where you
   launched `chenin app` (usually your project folder).
2. **Samples** — one row per report, *in core order*. Type the report file name and
   its `Depth top` / `Depth bottom` in centimetres. Use the **+** at the bottom of the
   table to add rows.
3. **Age model** *(optional)* — a base year and sedimentation rate produce an `Age`
   column. Leave blank to omit it.
4. **Nuclides** — one row per gamma peak. A nuclide is one or more peaks read from a
   report's section 3. Give several peaks the **same key** to combine them as a
   weighted mean (e.g. `RA-226` measured through its `PB-214`/`BI-214` daughters).
5. **Columns** — what ends up in the synthesis, in order. For each column fill exactly
   one of *Source* (a nuclide key from above) or *Formula* (arithmetic over nuclide
   keys, e.g. `pb210 - ra226`).

As you edit, the **Preview & export** section validates the file. When it's valid you
can either:

- **Download build file** — save the `.toml` to disk for reuse, or
- **Load into app** — use it right now (equivalent to loading it in the sidebar).

### Option B — write the TOML by hand

If you'd rather write the file in a text editor, the full schema (every key, every
rule) is in [`synthesis.md`](synthesis.md). A minimal example is in the
[README](../README.md#the-build-file). Save it as, say, `my_core.toml`.

## Step 2 — Load the build file

In the **sidebar**, use *Import a build file (.toml)* and pick your file. Chenin reads
each report listed under `base_path` and shows how many samples were loaded. This is
the single point of entry: every page reads from here.

If a report can't be found, you'll get a clear error naming the missing file — check
the file name in the build file and the `base_path` folder.

## Step 3 — Inspect the reports

Open the **Reports** page. There's one tab per loaded report, and inside each tab one
card per section (`s1`–`s6`). For every table you can:

- **Table / Pivot / Filter** — switch how the table is shown. *Pivot* lets you
  cross-tabulate; *Filter* gives per-column filters.
- **Export** — download that single section as CSV or Parquet.

This page is for checking that the parse looks right and for pulling out an individual
section — the synthesis itself is built on the next page.

## Step 4 — Build and read the synthesis

Open the **Synthesis** page. Chenin builds the table from your build file and shows it
in three parts:

- **Configuration** (collapsible) — a recap of the age model, nuclides and columns
  Chenin used, so you can confirm the build file did what you meant.
- **Core** — a vertical sediment-core view: each band is a sample from `depth_top` to
  `depth_bot`, coloured by an activity you choose (the *Colour layers by* selector).
  Depth increases downward, like a real core. Hover a band for its depth and value.
- **Profiles** — one small chart per nuclide: activity against depth, with 1σ error
  bars. This is the classic view for spotting the ²¹⁰Pb decrease or the ¹³⁷Cs peak.
- **Table** — the full synthesis, with the same Table / Pivot / Filter modes as the
  Reports page.

Each row has `Profondeur` (= `depth_top`), `Epaisseur` (= `depth_bot − depth_top`), an
`Activite <name>` and `Incertitude <name>` per column, and an `Age` column if you
configured an age model. Uncertainties are propagated automatically (see
[`measurement.md`](measurement.md)).

## Step 5 — Export

Under the synthesis table, use **Export** and pick a format:

- **CSV** — semicolon-separated, the general-purpose option.
- **Parquet** — compact binary, for loading back into pandas/R.
- **SERAC** — for the R `serac` age-depth modelling package.
  *(SERAC export is a work in progress.)*

## Doing it from the command line

Everything above has a command-line equivalent — useful for scripting or batch runs.

```sh
# Inspect one report
chenin extract path/to/report.txt          # all sections
chenin extract path/to/report.txt -s s3    # one section
chenin extract path/to/report.txt -o out/  # each section to a CSV in out/

# Build the synthesis from a build file
chenin synthesis my_core.toml              # print it
chenin synthesis my_core.toml -o out.csv   # export to CSV
```

For `synthesis`, report paths come from the build file (`base_path` + `[[samples]]`),
resolved relative to the build file's own folder — you don't list them on the command
line.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| *"report not found for sample …"* | The file name in `[[samples]]` doesn't match a file under `base_path`, or `base_path` is wrong. Paths are relative to where you launched Chenin. |
| *"Invalid build file: …"* | A validation error — the message names the problem (missing depth, unknown nuclide, a column with both `source` and `formula`, …). See the error table in [`synthesis.md`](synthesis.md#erreurs-de-configuration). |
| A nuclide column is empty (NaN) | No section-3 peak matched within 1 keV of the configured energy, or the report doesn't report that nuclide. Check the energy and the nuclide name against the Reports page. |
| The `Age` column is missing | The age model isn't configured — set both a base year and a sedimentation rate in the build file. |
| `chenin: command not found` | The tool install didn't add `chenin` to PATH, or you're in a clone — use `uv run chenin ...` instead. |

For the complete build-file reference, see [`synthesis.md`](synthesis.md). For how
uncertainties are combined, see [`measurement.md`](measurement.md).
