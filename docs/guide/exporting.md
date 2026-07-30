# Exporting

Nothing Chenin does is saved automatically. Reports live in the browser session, and
closing the tab loses them. Export whatever you want to keep.

## From the app

**Per section** (Reports page) — the *Export* button on each section saves that one table.
It saves **what is currently on screen**, so if you filtered the view, you export the
filtered rows. That is the easiest way to get just the ²¹⁰Pb rows out of section 3.

**Everything at once** (Reports page) — *Export all (ZIP)* saves every section of every
loaded report as `report-name/section.csv` inside a single zip. Good for archiving a
batch.

**The synthesis** — export it from the preview panel of whichever column-builder tab you
used.

## The formats

### CSV

The default. Written for Excel in a French locale:

- `;` as the field separator
- six decimal places on every number
- no row index column

Opening it in Excel with a French regional setting works directly. With an English setting,
Excel will put every row in one cell — use *Data → From Text/CSV* and pick semicolon as the
delimiter.

### Parquet

A compact binary format that keeps column types exactly. Use it if the next step is Python
or R rather than a spreadsheet: it loads faster, cannot mangle a number, and does not care
about locales.

### SERAC

A ready-made input file for the [serac](https://github.com/EDYTEM/serac) R package, which
does the age-depth modelling. Tab-separated, **depths converted from cm to mm**, with the
columns serac expects:

```
depth_top  depth_bottom  density  Pbex  Pbex_er  Cs  Cs_er  Am  Am_er
```

The mapping from your synthesis is:

| serac column | Comes from |
|---|---|
| `depth_top` | `Profondeur` × 10 |
| `depth_bottom` | (`Profondeur` + `Epaisseur`) × 10 |
| `density` | `DBD` |
| `Pbex` / `Pbex_er` | `Activite PB-Exc` / `Incertitude PB-Exc` |
| `Cs` / `Cs_er` | `Activite CS-137` / `Incertitude CS-137` |
| `Am` / `Am_er` | `Activite AM-241` / `Incertitude AM-241` |

Rows with no activity for any of the three nuclides — planned but unmeasured layers — are
dropped, because serac has nowhere to put them.

**Two prerequisites.** Your synthesis must contain `PB-Exc`, `CS-137` and `AM-241` columns
under exactly those names (the packaged default template provides all three), and **`DBD`
must be filled in** on the core layers grid — serac needs density, and Chenin cannot invent
it.

If a required column is missing you get an error naming it and listing what the synthesis
actually has.

> **Currently the SERAC format is not offered by any export button in the app.** The code
> is complete and tested by hand, but no page passes it to the export widget yet, so it is
> only reachable from Python:
>
> ```python
> from chenin import export_serac
> Path("core.serac").write_bytes(export_serac(synthesis_df))
> ```
>
> This is tracked in
> [known issues](https://github.com/Ezacuak/chenin/blob/main/docs/dev/known-issues.md).

## From the command line

```sh
chenin extract report.txt -o out/          # every section as CSV into out/
chenin synthesis data/NOIR24-01/ -o synthesis.csv
```

See [Command Line](https://github.com/Ezacuak/chenin/blob/main/docs/guide/command-line.md).
