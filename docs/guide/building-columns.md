# Building Columns

> **This section of the app is an experiment.** It currently holds **five competing
> designs** for the same job, shown as five tabs. They are a deliberate bake-off: the lab
> is meant to try them and pick one, after which the other four will be deleted. Do not
> read this page as five features — it is one feature, drawn five ways.

## What they all have in common

Every tab produces exactly the same thing: a **list of columns**, where each column is one
of three kinds.

| Kind | Where its value comes from | Output |
|---|---|---|
| **Geometry** | The core layers grid | `Echantillon`, `Profondeur`, `Epaisseur`, `DBD` |
| **Measured** | Gamma peaks in section 3 | `Activite X` + `Incertitude X` |
| **Derived** | A formula over measured columns | `Activite X` + `Incertitude X` |

That list is handed to the same builder in every case, so the numbers do not depend on
which tab you used. Only the way you *say what you want* differs.

Three consequences:

- The four geometry columns are added automatically if you do not declare any.
- Every tab shows a live preview built from your real reports — there is no separate
  "preview mode" that might disagree with the real output.
- **All five tabs write to the same stored synthesis, so the last tab you looked at wins.**
  If you build columns in one tab, then click another, the second tab's version is what
  gets exported. Settle on one tab per session.

## The five designs

### Data catalog

One big editable grid listing every column you could have — geometry, measured, derived —
with a tick box on each. The **Coverage** column tells you how many of your selected
reports actually contain that line, so you can see at a glance that `AM-241` is only in
half the core.

Three presets fill the grid in one click: *Standard 210Pb / 137Cs*, *Everything*, and
*SERAC ready*. The **Peaks / formula** cell is editable, so this is also the fastest way to
hand-edit one method.

*Best if you already know what you want and just want to tick it.*

### Guided wizard

A four-step flow: confirm the layers, choose the nuclides, add derived columns, see the
result. Step 1 is a read-only recap with the layer count, the depth range and how many
reports were excluded — a last chance to spot a geometry mistake before building.

Excess ²¹⁰Pb is a toggle with an editable formula rather than something you have to know to
write.

*Best for a first synthesis, or for someone who has not done this in six months.*

### Peak-first

Starts from what is actually in your spectra, not from a list of nuclides. It inventories
every gamma line found across the selected reports, with its coverage, mean activity and
typical uncertainty, and you tick the lines you want.

The **Goes into column** cell is the interesting part: give two lines the same column name
and they are combined into one weighted mean. That is `RA-226` built by hand from ²¹⁴Pb and
²¹⁴Bi progeny — visible rather than declared.

*Best when you are exploring an unfamiliar core, or deciding which lines are usable.*

### Template editor

Edits the [template](https://github.com/Ezacuak/chenin/blob/main/docs/guide/synthesis-template.md)
itself — the two-row CSV — as a grid. Load the lab default, upload an existing template,
add columns, download the result.

What you download is parsed back through the real template parser before the preview, so
the file you save is guaranteed to rebuild what you saw. It is the only tab whose output is
a reusable artefact, and the only one that matches what `chenin synthesis -t` does.

*Best when the lab wants one agreed column set used by everyone, every time.*

### Core canvas

The core itself is the interface: a stacked bar of your layers, coloured by any column.
Click a band and the panel beside it shows that sample's computed columns **and the raw
section 3 rows behind them**.

Column choice is tucked into an expander, because the point of this design is checking
results rather than declaring them — it answers "why is this value weird?" in two clicks.

*Best for reviewing a finished synthesis rather than defining one.*

## Choosing between them

If you have no opinion: use **Template editor** if the lab wants one shared column set,
**Guided wizard** if you are new, **Core canvas** to inspect what came out.

Feedback on which to keep is the whole point of this section — that is the decision the
bake-off exists to make.
