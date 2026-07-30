# Core Layers

This page covers the first three sections of the Synthesis page — everything you set up
*before* choosing columns.

## 1. Reports selection

Pick which of the loaded reports belong to this synthesis. Anything you leave out is
ignored entirely: it will not appear as a row, and its gamma lines will not be offered when
you build columns.

Use this to exclude calibration standards (RGU1, RGTh, IAEA-447) and re-measurements that
happen to sit in the same folder as the core.

## 2. Nuclide Library

The library is the list of nuclides Chenin knows about, and for each one, the gamma
energies it should look for. It is what populates the peak menus further down the page.

**Adding one** — type a name and its energies, then save. The name is normalised
automatically, so `210pb`, `Pb-210` and `pb 210` all become `PB-210`. Energies are in keV,
comma-separated: `295.21, 351.92`.

**The defaults** are `CS-137` (661.7), `PB-210` (46.5), `Th-228` (238.6), `K-40` (1460.8),
`AM-241` (59.5).

**Active library** lists what is currently loaded, with a delete button per nuclide.

### Saving and sharing a library

The sidebar (visible while you are on the Synthesis page) has the import/export controls:

- **Download library (JSON)** — save your library to a file.
- **Load library file** + **Apply loaded file** — restore one. Accepts JSON
  (`{"PB-210": [46.5]}`) or CSV with `Nuclide` and `Peaks` columns, where `Peaks` is a
  comma-separated list.
- **Reset to default** — back to the five nuclides above.

Sharing that JSON file is how a lab keeps everyone on the same energies.

## 3. Core layers

This is where the core's geometry is entered: one row per report, with a top depth, a
bottom depth, and optionally a dry bulk density.

**Génie 2000 reports contain no depth information.** There is nothing in the file that says
"this sample came from 6 cm down". Chenin cannot infer it, so you provide it — either by
typing it, or by generating it from a slicing rule.

### Generating depths from a slicing rule

Open **Generate depths from a slicing rule**, set the start depth and the slice thickness,
choose how slices are numbered, and click **Fill the table**. This only *prefills* the
grid — every cell stays editable afterwards, so you can fix the one slice that was cut
differently.

### The slice-number rule, and why it matters

The depth of a slice is:

```
depth_top = start + (n - 1) × thickness
```

The question is what `n` is, and that is what the **Slice number** choice decides.

**From the file name** (the default) reads the trailing number of the report name:
`NOI_S_13` gives `n = 13`. **Sequential** ignores the name and uses the report's position
in the sorted list instead.

They differ exactly when slices are missing. Take a real core, NOIR24-01: thirteen reports
exist, but slices **12, 14 and 15 were never measured**. With 0.5 cm slices starting at 0:

| Report | From the file name | Sequential |
|---|---|---|
| `NOI_S_11` | 5.0 cm | 5.0 cm |
| `NOI_S_13` | **6.0 cm** | **5.5 cm** |
| `NOI_S_16` | **7.5 cm** | **6.0 cm** |

"From the file name" keeps `NOI_S_13` at its true 6.0 cm. "Sequential" slides it up into
the hole left by the missing slice 12, and every subsequent slice inherits the error — by
`NOI_S_16` the depth is off by 1.5 cm. **In an age-depth model that is not a rounding
error, it is a wrong answer.**

Use "From the file name" unless your reports genuinely are not numbered by slice. A report
whose name ends in no digits falls back to its position in the list.

Reports are sorted naturally, so `NOI_S_2` comes before `NOI_S_10`, not after it.

### The grid

| Column | Meaning |
|---|---|
| Report | Which loaded report this row is. Fixed — it comes from section 1. |
| Sample | The sample code written to the output. Defaults to the report name. |
| Depth top (cm) | Top of the slice. |
| Depth bottom (cm) | Bottom of the slice. `Epaisseur` in the output is bottom − top. |
| DBD (g/cm³) | Dry bulk density. Optional here, but **required by SERAC export** — fill it if you plan to export for age modelling. |

Depths are the only mandatory fields. A row missing either one is excluded from the
synthesis, and the page tells you which rows those are.

### The three warnings

Below the grid, Chenin checks your geometry and tells you about:

- **Excluded rows** — a report with no usable depths. It will not appear in the output at
  all.
- **Overlapping layers** — two slices claim the same depth. Almost always a typo; the
  builder will happily produce both rows, and your age model will not thank you.
- **Unmeasured intervals** — gaps between slices, listed as depth ranges. Often expected
  (that is exactly the missing-slice case above), which is why this is an informational
  note and not an error. Worth a glance to confirm the gaps are the ones you expect.

## Doing this from the command line

The same rule drives `chenin synthesis`:

```sh
chenin synthesis data/NOIR24-01/ --start 0 --thickness 0.5
chenin synthesis data/NOIR24-01/ --thickness 0.5 --sequential
```

`--sequential` is the "Sequential" radio button. The CLI cannot set per-slice DBD or fix an
individual slice — for that, use the app. See
[Command Line](https://github.com/Ezacuak/chenin/blob/main/docs/guide/command-line.md).
