# Templates

A **template** is a small CSV that says which columns your synthesis has and how each one
is computed. It is the only configuration file Chenin reads, and it is deliberately small
enough to edit in Excel.

## The shape: two rows

Row 1 is the **column names** you want in the output. Row 2 is the **method** for each —
how to compute it. That is the whole format.

```csv
PB-210,RA-226,PB-Exc,AM-241,CS-137,K-40
PB-210@46.54,PB-214@295.21; PB-214@351.92; BI-214@609.31,=[PB-210] - [RA-226],AM-241@59.54,CS-137@661.66,K-40@1460.82
```

That is the packaged lab default, in full. Laid out per column it reads:

| Column name | Method | Meaning |
|---|---|---|
| `PB-210` | `PB-210@46.54` | ²¹⁰Pb on its 46.54 keV line |
| `RA-226` | `PB-214@295.21; PB-214@351.92; BI-214@609.31` | ²²⁶Ra via three daughter lines, combined |
| `PB-Exc` | `=[PB-210] - [RA-226]` | excess ²¹⁰Pb, computed |
| `AM-241` | `AM-241@59.54` | ²⁴¹Am on 59.54 keV |
| `CS-137` | `CS-137@661.66` | ¹³⁷Cs on 661.66 keV |
| `K-40` | `K-40@1460.82` | ⁴⁰K on 1460.82 keV |

`.xlsx` files work too — the reader picks itself by file extension — but plain CSV is
easier to diff and share.

## Method cells: two forms

### Peaks — `NUCLIDE@energy`

The nuclide name must match section 3 of the report **exactly**; the energy is matched to
the nearest line within 1.0 keV.

Several peaks separated by `;` are combined into one inverse-variance weighted mean:

```
PB-214@295.21; PB-214@351.92; BI-214@609.31
```

**The nuclide in the peak has nothing to do with the column name.** That is the point of
the `RA-226` column above: ²²⁶Ra has no usable direct line here, so it is measured through
its ²¹⁴Pb and ²¹⁴Bi daughters. Spaces around the `;` are fine.

### Formulas — `=expression`

A cell starting with `=` is arithmetic over the other columns, referenced in square
brackets:

```
=[PB-210] - [RA-226]
```

Full syntax in
[Formulas](https://github.com/Ezacuak/chenin/blob/main/docs/guide/formulas.md). The `=`
must be the first character — otherwise the cell is read as a peak list.

## What comes out

Every column in the template becomes **two** output columns, an activity and its
uncertainty, both prefixed:

```
Activite PB-210, Incertitude PB-210, Activite RA-226, Incertitude RA-226, ...
```

In front of those, four **geometry** columns are always written, carrying the layer's own
numbers rather than any measurement:

| Output column | Content |
|---|---|
| `Echantillon` | Sample code |
| `Profondeur` | Depth of the top of the slice, cm |
| `Epaisseur` | Slice thickness (bottom − top), cm |
| `DBD` | Dry bulk density, g/cm³ |

Geometry columns are not written in the template — they are added automatically. Column
order in the output is: the four geometry columns, then your template columns left to
right. Rows are sorted by depth.

## Using a template

**In the app** — the Synthesis page's *Template editor* tab loads, edits and downloads
templates, and round-trips through the same parser, so what you download rebuilds exactly
what you saw.

**On the command line:**

```sh
chenin synthesis data/NOIR24-01/ -t my_template.csv --thickness 0.5
```

Omit `-t` and the packaged default above is used.

## Rules and gotchas

- **At least one peak column is required.** A template of nothing but formulas is rejected:
  there would be nothing to compute from.
- **Every named column needs a method.** A blank method cell is an error, not an empty
  column.
- **Only the first data row is read.** Anything below row 2 is ignored — handy for notes,
  but do not expect it to do anything.
- **Blank header cells are skipped**, so trailing commas are harmless.
- **Avoid two columns whose names differ only in punctuation.** `PB-210` and `PB 210` map
  to the same internal key, and the second silently overwrites the first.

## Errors

| Message | Cause |
|---|---|
| `synthesis template has no method row` | The file has a header but no second row. |
| `column 'X' has no method` | Named column with an empty method cell. |
| `synthesis template has no measured (peak) columns` | Every column is a formula. |
| `column 'X': peak 'y' must be NUCLIDE@energy` | A peak with no `@`. |
| `column 'X': peak 'y' has an invalid energy` | The text after `@` is not a number. |
