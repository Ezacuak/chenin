# Chenin — user guide

This guide walks you through Chenin end to end: from a folder of raw Génie 2000
reports to an activity-vs-depth synthesis you can export for age-depth modelling.
No prior programming experience is required.

- [Concepts](#concepts)
- [Install](#install)
- [Launch the app](#launch-the-app)
- [Step 1 — Write a roadmap](#step-1--write-a-roadmap)
- [Step 2 — Load the roadmap](#step-2--load-the-roadmap)
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
- **Roadmap** — a spreadsheet (`.csv` or `.xlsx`) that lists the core's samples: one
  row per layer, with its report file, depths and density. One roadmap describes one
  core. It's the single file you write.
- **Synthesis** — the result: a table with **one row per sample**, each nuclide's
  activity and uncertainty, and the depth. This is what you export. Which nuclides
  appear is set by a **synthesis template**; the standard one ships with Chenin, so you
  usually don't touch it.

The flow is always the same:

```
reports (.txt)  +  depths        →  roadmap (.csv)  →  synthesis (table)
                (you provide)        (one per core)      (one row per sample)
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
**Home**, **Roadmap**, **Reports**, **Synthesis** — and you work left to right through
them, starting on **Roadmap** where you load your file.

> Prefer the command line? Skip to
> [Doing it from the command line](#doing-it-from-the-command-line). The app and the
> CLI use the exact same roadmap and produce the exact same synthesis.

## Step 1 — Write a roadmap

A roadmap is an ordinary spreadsheet — edit it in Excel or LibreOffice and save as
`.csv` or `.xlsx`. It has one row per sample and these columns:

| Column | What to put |
|---|---|
| `LSM Code` | The core's identifier (e.g. `NOIR24-01`). Same on every row. |
| `Sample Code` | A readable id for the sample (e.g. `NOI24-01-1`). |
| `Depth Top` | Depth of the top of the layer, in centimetres. |
| `Depth Bot` | Depth of the bottom of the layer, in centimetres. |
| `DBD` | Dry bulk density (leave `0` if unknown for now). |
| `G2K Report` | The report file name (e.g. `NOI_S_1.txt`). **Leave empty** for a planned but not-yet-measured layer. |

```csv
LSM Code, Sample Code, Depth Top, Depth Bot, DBD, G2K Report
NOIR24-01, NOI24-01-1, 0.0, 0.5, 0, NOI_S_1.txt
NOIR24-01, NOI24-01-2, 0.5, 1.0, 0, NOI_S_2.txt
NOIR24-01, NOI24-01-3, 1.0, 1.5, 0,
```

Keep the report files in the **same folder** as the roadmap. On the Roadmap page you
can **download a blank roadmap template** to start from.

That's all most cores need. The standard nuclide columns (PB-210, RA-226, PB-Exc,
AM-241, CS-137, K-40) come from a built-in template. To change them, see the
*custom synthesis template* section of [`synthesis.md`](synthesis.md#le-template-de-synthèse).

## Step 2 — Load the roadmap

Open the **Roadmap** page:

1. **Upload** your roadmap `.csv`/`.xlsx`.
2. Set the **Reports folder** — the folder that holds the `.txt` reports (relative to
   where you launched `chenin app`, or an absolute path).
3. Check the preview table, then click **Load into app**.

Chenin reads each report and shows how many samples were loaded. Rows with an empty
`G2K Report` are kept as depth-only rows. This is the single point of entry: every
other page reads from here.

If a report can't be found, you'll get a clear error naming the missing file — check
the file name in the roadmap and the Reports folder.

## Step 3 — Inspect the reports

Open the **Reports** page. There's one tab per loaded report, and inside each tab one
card per section (`s1`–`s6`). For every table you can:

- **Table / Pivot / Filter** — switch how the table is shown. *Pivot* lets you
  cross-tabulate; *Filter* gives per-column filters.
- **Export** — download that single section as CSV or Parquet.

This page is for checking that the parse looks right and for pulling out an individual
section — the synthesis itself is built on the next page.

## Step 4 — Build and read the synthesis

Open the **Synthesis** page. Chenin builds the table from your roadmap and shows it in
several parts:

- **Configuration** (collapsible) — a recap of the nuclides and columns Chenin used, so
  you can confirm the template did what you meant.
- **Core** — a vertical sediment-core view: each band is a sample from `Depth Top` to
  `Depth Bot`, coloured by an activity you choose (the *Colour layers by* selector).
  Depth increases downward, like a real core. Hover a band for its depth and value.
- **Profiles** — one small chart per nuclide: activity against depth, with 1σ error
  bars. This is the classic view for spotting the ²¹⁰Pb decrease or the ¹³⁷Cs peak.
- **Table** — the full synthesis, with the same Table / Pivot / Filter modes as the
  Reports page.

Each row has `Echantillon` (the sample code), `Profondeur` (= `Depth Top`), `Epaisseur`
(= `Depth Bot − Depth Top`), `DBD`, and an `Activite <name>` / `Incertitude <name>`
pair per column. Depth-only layers show their geometry with blank activities.
Uncertainties are propagated automatically (see [`measurement.md`](measurement.md)).

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

# Build the synthesis from a roadmap
chenin synthesis my_core.csv               # print it (default template)
chenin synthesis my_core.csv -o out.csv    # export to CSV
chenin synthesis my_core.csv --template my_template.csv   # custom columns
```

For `synthesis`, report paths come from the roadmap's `G2K Report` column, resolved
next to the roadmap file — you don't list them on the command line.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| *"report not found for sample …"* | The `G2K Report` name doesn't match a file in the Reports folder (CLI: next to the roadmap). Paths are relative to where you launched Chenin. |
| *"Invalid roadmap: …"* | A validation error — the message names the problem (missing depth, malformed peak, a template column with no method, …). See the error table in [`synthesis.md`](synthesis.md#erreurs-de-configuration). |
| A nuclide column is empty (NaN) | Either the row has no report (depth-only), or no section-3 peak matched within 1 keV of the template energy. Check the energy and nuclide name against the Reports page. |
| `chenin: command not found` | The tool install didn't add `chenin` to PATH, or you're in a clone — use `uv run chenin ...` instead. |

For the complete roadmap and template reference, see [`synthesis.md`](synthesis.md). For
how uncertainties are combined, see [`measurement.md`](measurement.md).
