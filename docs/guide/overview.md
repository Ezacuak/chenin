# Overview

Chenin turns **Génie 2000 gamma-spectrometry reports** into a **synthesis table** you can
hand to an age-depth model.

Génie 2000 (G2K) writes one plain-text report per measured sample. Each report says which
nuclides were identified, on which gamma lines, and at what activity — but it says nothing
about *where in the core* that sample came from. Chenin reads a whole folder of those
reports, attaches the depth of each slice, and produces one row per sample with the
activities and uncertainties you actually want:

| Echantillon | Profondeur | Epaisseur | DBD | Activite PB-210 | Incertitude PB-210 | … |
|---|---|---|---|---|---|---|
| NOI_S_1 | 0.0 | 0.5 | | 285.4 | 14.1 | … |
| NOI_S_2 | 0.5 | 0.5 | | 271.9 | 13.6 | … |

That table is the input to excess-²¹⁰Pb dating (the `serac` R package, the lab workbook, or
anything else that eats a depth/activity table).

## The workflow

Chenin has three steps, and the app's sidebar follows them in order.

1. **Load Data** — upload your `.txt` reports. Each one is parsed into seven sections.
2. **Reports** — browse what was extracted, section by section, and export any of it.
3. **Synthesis** — pick the reports, declare the depths, choose the columns, get the table.

Everything the app does is also available from the command line — see
[Command Line](https://github.com/Ezacuak/chenin/blob/main/docs/guide/command-line.md).

## Vocabulary

These words mean something specific in Chenin. They are used consistently throughout the
documentation and the interface.

| Term | Meaning |
|---|---|
| **Report** | One G2K `.txt` file: one measured sample. Its name (e.g. `NOI_S_13`) is used as the sample identifier. |
| **Section** | One `*****TITLE*****` block inside a report. There are seven, keyed `s1`–`s6` (section 4 splits in two). |
| **Slice / Layer** | A depth interval of the core: a top depth, a bottom depth, and optionally a dry bulk density. Reports carry no depth, so you supply this. |
| **Nuclide** | A radioisotope, written canonically as `PB-210`, `CS-137`, `RA-226`. Chenin normalises `210pb`, `Pb-210` and `pb 210` to the same thing. |
| **Peak / Line** | One gamma emission energy in keV, e.g. `PB-210@46.54`. A nuclide can be measured on several lines. |
| **Activity** | Specific activity in mBq/g, read from section 3 of the report. |
| **Uncertainty** | The 1σ uncertainty on an activity, always carried alongside it and propagated through every calculation. |
| **Measured column** | A synthesis column whose value comes from gamma peaks. |
| **Derived column** | A synthesis column computed from other columns by a formula, e.g. `PB-Exc = PB-210 − RA-226`. |
| **Geometry column** | A synthesis column that carries the layer's own numbers, not a measurement: sample code, depth, thickness, density. |
| **Template** | A small CSV describing which columns your synthesis should have and how each is computed. |

## Two things that surprise people

**Column names in the output are French.** `Echantillon`, `Profondeur`, `Epaisseur`, `DBD`,
`Activite …`, `Incertitude …`. This is deliberate — those names feed SERAC and the lab's
downstream workbooks. The interface and this documentation are English; the data columns
are not, and should not be translated.

**A nuclide is not always measured on its own line.** ²²⁶Ra has no usable direct gamma
line in these spectra, so it is measured through its daughters ²¹⁴Pb and ²¹⁴Bi. That is why
the default template's `RA-226` column reads
`PB-214@295.21; PB-214@351.92; BI-214@609.31` — three lines from two different nuclides,
combined into one weighted mean. The column name and the nuclide named in the peaks are
independent.

## Where to go next

- Never installed it: [Install & Update](https://github.com/Ezacuak/chenin/blob/main/docs/guide/install.md)
- Have reports, want a table: [Loading Reports](https://github.com/Ezacuak/chenin/blob/main/docs/guide/loading-reports.md), then [Core Layers](https://github.com/Ezacuak/chenin/blob/main/docs/guide/core-layers.md)
- Want to compute excess ²¹⁰Pb: [Formulas](https://github.com/Ezacuak/chenin/blob/main/docs/guide/formulas.md)
- Something went wrong: [Troubleshooting](https://github.com/Ezacuak/chenin/blob/main/docs/guide/troubleshooting.md)
