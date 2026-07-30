# Troubleshooting

## A report will not load

**`Format de rapport inattendu pour la section sN : motif d'en-tete introuvable.`**

The report's layout does not match what Chenin expects for that section. Chenin refuses to
guess, because a misaligned table would put activities in the wrong column and look
perfectly plausible.

Usual causes, in order of likelihood:

1. **It is not a Génie 2000 report** — a CSV export, a PDF converted to text, or a report
   from different software.
2. **Génie 2000 was reconfigured** — a changed report template adds, removes or reorders
   columns.
3. **The file was edited** — opened in Word, re-saved with different line endings, or had a
   header trimmed.

Compare the failing file against one that loads. If Génie 2000's output has genuinely
changed at the lab, the parser needs updating — that is a code change, see the
[developer docs](https://github.com/Ezacuak/chenin/blob/main/docs/dev/parsing-g2k.md).

**Sections come out shifted or empty** — a section is identified by its *position* among
the banner blocks, not by its title. A report missing one block shifts every later section
by one. Check the file has all six `*****TITLE*****` banners.

## A nuclide is blank in the synthesis

A blank means "no usable measurement", not "an error". Work through it in this order:

1. **Is it in section 3?** Open the report on the Reports page and look. If the nuclide is
   not listed, Génie 2000 did not identify it in that sample — genuinely absent, and blank
   is the correct answer.
2. **Is the energy right?** A peak matches the nearest line within **1.0 keV**. If your
   template says `PB-210@46.5` but section 3 lists 48.2 keV, nothing matches. Copy the
   energy from section 3.
3. **Is the nuclide name right?** It must match section 3 *exactly*: `PB-210`, not `Pb-210`
   or `210Pb`, when that is how the report writes it.
4. **Does it have an uncertainty?** A line with a missing or zero uncertainty is skipped
   when combining peaks. If it is the only line, the column is blank.

**A derived column is blank wherever its inputs are.** If `RA-226` is blank for a sample,
`PB-Exc` is blank there too. That is deliberate: a partial subtraction would be a made-up
number.

## The depths are wrong

Almost always the slice-numbering rule. Check the **Slice number** setting: *From the file
name* reads the trailing number of the report name, *Sequential* uses list position. They
diverge as soon as one slice is missing, and every slice below the gap inherits the error.

The full explanation, with a worked example, is in
[Core Layers](https://github.com/Ezacuak/chenin/blob/main/docs/guide/core-layers.md).

If a single slice was cut differently, type its depths directly into the grid — the
generator only prefills, the cells stay editable.

## "Unmeasured intervals" and "Overlapping layers"

**Unmeasured intervals** is informational. Gaps are normal in a core where some slices were
never measured. Read the listed ranges and confirm they are the gaps you expect.

**Overlapping layers** is worth acting on. Two slices claiming the same depth is almost
always a typo in the grid. The synthesis will still build, with both rows present.

## A template is rejected

| Message | Fix |
|---|---|
| `synthesis template has no method row` | Add the second row — the file needs names *and* methods. |
| `column 'X' has no method` | That column's method cell is empty. Fill it, or delete the header. |
| `synthesis template has no measured (peak) columns` | Every column is a formula. At least one must read real peaks. |
| `column 'X': peak 'y' must be NUCLIDE@energy` | A peak is missing its `@`. Write `PB-210@46.54`. |
| `column 'X': peak 'y' has an invalid energy` | The text after `@` is not a number — check for a stray unit or a comma decimal separator. |

Format reference:
[Templates](https://github.com/Ezacuak/chenin/blob/main/docs/guide/synthesis-template.md).

## A formula is rejected

| Message | Fix |
|---|---|
| `invalid syntax` | Not valid arithmetic — a dangling operator or unclosed bracket. |
| `unknown nuclide 'x' in formula` | No column by that name. Note that formulas cannot reference **other formulas**, only measured columns. |
| `operator Pow is not allowed` | Only `+ - * /` exist. No `**`, `^`, `%`. |
| `unsupported expression element: Call` | No functions. There is no `sqrt()`. |
| `division by zero` | The denominator came out exactly zero. |

Try it on the
[Formula Tester](https://github.com/Ezacuak/chenin/blob/main/docs/guide/formula-tester.md)
page — same evaluator, immediate feedback. Full syntax in
[Formulas](https://github.com/Ezacuak/chenin/blob/main/docs/guide/formulas.md).

## My reports disappeared

Loaded reports live in the browser session. Restarting the app, reloading the page after
the server stopped, or letting the session time out all clear them. Nothing is written to
disk. Re-upload, and export anything you need to keep.

## SERAC export fails

`synthesis has no 'Activite X'/'Incertitude X' column` — your synthesis does not have the
columns SERAC needs (`PB-Exc`, `CS-137`, `AM-241` by default). Use the packaged default
template, or map your own names.

Also check `DBD` is filled in on the core layers grid. SERAC needs density and Chenin
cannot invent it. A synthesis built from the command line never has DBD.

## `chenin: command not found`

The install did not finish, or your terminal predates it. Open a **new** terminal and try
again. If it still fails, re-run:

```sh
uv tool install git+https://github.com/Ezacuak/chenin.git
```

and check `uv --version` works first — if that fails too, the problem is the uv install.
See [Install & Update](https://github.com/Ezacuak/chenin/blob/main/docs/guide/install.md).

## Numbers look wrong in Excel

CSV exports use `;` as the separator and a `.` decimal point. If every row lands in one
cell, Excel is expecting a comma: use *Data → From Text/CSV* and choose semicolon.

If your Excel is in a French locale and shows text where numbers should be, it is reading
`.` as a thousands separator — same import dialog, set the decimal separator explicitly.
Or export Parquet and skip the problem.
