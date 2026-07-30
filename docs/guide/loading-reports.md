# Loading Reports

## What a G2K report is

Génie 2000 exports one plain-text file per measured sample. The file is split into blocks
by banner lines that look like this:

```
*******************************************
*****        NUCLIDE IDENTIFICATION   *****
*******************************************
```

Chenin splits on those banners and turns each block into a table. Every report yields the
same seven tables:

| Key | Content |
|---|---|
| `s1` | Spectrum analysis report (metadata) — acquisition date, live time, sample ID, geometry. One row. |
| `s2` | Peak analysis report — every peak found in the spectrum: channel, energy, FWHM, net area. |
| `s3` | Nuclide identification report — **the one that matters**: nuclide, energy, activity in mBq/g, uncertainty. |
| `s4_nucleides` | Identification with interference correction — nuclides sub-table. |
| `s4_pics` | Identification with interference correction — peaks sub-table. |
| `s5` | Detection limits report. |
| `s6` | Detection limits report (ISO 11929). |

**Section 3 is where every synthesis number comes from.** When a nuclide comes out blank in
your synthesis, section 3 of that report is the first place to look.

Sections are identified by *position*, not by the text of their banner. A report with a
missing or extra banner block will be misread — see
[Troubleshooting](https://github.com/Ezacuak/chenin/blob/main/docs/guide/troubleshooting.md).

## The Load Data page

Drag your `.txt` reports onto the uploader, or click to browse. You can select many files
at once, and you should: the synthesis needs the whole core.

Each file is parsed immediately. A file that fails to parse produces a red message naming
it, and is skipped — the others still load. When it succeeds you get a green confirmation
and a list of the loaded report names.

**The report name is its file name without the extension.** `NOI_S_13.txt` becomes the
report `NOI_S_13`. That name is used as the default sample code, and — importantly — the
trailing number is used to work out the slice depth. See
[Core Layers](https://github.com/Ezacuak/chenin/blob/main/docs/guide/core-layers.md).

Re-uploading the same set of files does not re-parse them. Change the selection to reload.

Loaded reports live in the browser session. **Closing the tab or restarting the app loses
them** — nothing is written to disk. Export anything you want to keep.

## The Reports page

One tab per loaded report, and inside each tab one bordered block per section, labelled
with the descriptions from the table above.

### Three ways to look at a table

Each section has a small **Display** switch:

- **Table** — the plain data, sortable by clicking a column header.
- **Pivot** — drag fields into rows/columns/values to cross-tabulate.
- **Filter** — build filters on the columns (ranges for numbers, checkboxes for categories)
  and see the subset.

The switch changes what you see *and* what you export: the export button always saves the
frame currently on screen, filters included. That is the easy way to get "just the ²¹⁰Pb
rows from section 3".

### Exporting

- The **Export** button on each section saves that one table, as CSV or Parquet.
- The **Export all (ZIP)** button at the top of the page saves *every section of every
  report* as `report-name/section.csv` inside one zip.

Details of the formats are in
[Exporting](https://github.com/Ezacuak/chenin/blob/main/docs/guide/exporting.md).

## Column names

The extracted columns keep Génie 2000's French names, with accents removed and unit padding
cleaned up — `Activite (mBq/g)`, not `Activité (mBq/g   )`. They are fixed constants, so a
column name never changes between reports, and downstream scripts can rely on them.
