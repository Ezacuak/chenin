# Formulas

A **derived column** is computed from other columns instead of being read from a spectrum.
The canonical example is excess ²¹⁰Pb, which is total ²¹⁰Pb minus supported ²¹⁰Pb:

```
=[PB-210] - [RA-226]
```

This page is the complete reference for what you can write there.

## The rules, in one box

- A formula **starts with `=`**. Without it, the cell is read as a peak list instead.
- You refer to another column by its **display name in square brackets**: `[PB-210]`.
- The only operators are **`+`, `-`, `*`, `/`**, plus a leading `-` or `+`.
- **Parentheses** work and mean what you expect.
- **Plain numbers** are allowed: `=[PB-210] / 1000`.
- Uncertainties propagate automatically. You never write them.

Anything else — functions, powers, comparisons — is rejected. There is no `sqrt()`, no
`log()`, no `^`.

## Why the square brackets

Because `PB-210` is not a valid name. Without brackets it would be read as arithmetic:
"PB minus 210". The brackets tell Chenin "this whole thing is one column name", so any
display name works no matter what characters it contains.

Brackets are matched loosely: `[PB-210]`, `[pb 210]` and `[Pb_210]` all refer to the same
column. Case and punctuation do not matter; the letters and digits do.

## Worked example: excess ²¹⁰Pb

Say a sample measures:

| Column | Activity (mBq/g) | 1σ |
|---|---|---|
| PB-210 | 285.0 | 14.0 |
| RA-226 | 96.0 | 5.5 |

With `PB-Exc` defined as `=[PB-210] - [RA-226]`:

```
value = 285.0 - 96.0                  = 189.0
1σ    = √(14.0² + 5.5²) = √(196 + 30.25) = 15.04
```

The output gains two columns, `Activite PB-Exc` = 189.000 and `Incertitude PB-Exc` = 15.042.

You can check this yourself on the
[Formula Tester](https://github.com/Ezacuak/chenin/blob/main/docs/guide/formula-tester.md)
page, which runs the real evaluator on values you can edit.

## How uncertainty propagates

All propagation assumes the inputs are **uncorrelated**. `a` and `b` are measurements with
1σ uncertainties σa and σb.

| Operation | Result value | Result 1σ |
|---|---|---|
| `a + b` | a + b | √(σa² + σb²) |
| `a - b` | a − b | √(σa² + σb²) |
| `a * b` | a × b | \|a×b\| × √((σa/a)² + (σb/b)²) |
| `a / b` | a ÷ b | \|a÷b\| × √((σa/a)² + (σb/b)²) |
| `-a` | −a | σa — unchanged |
| number | the number | 0 |

Addition and subtraction add **absolute** uncertainties in quadrature; multiplication and
division add **relative** ones. Note that subtraction does *not* reduce the uncertainty —
`PB-Exc` above is less certain than either input, which is correct and is why excess ²¹⁰Pb
gets noisy as you go down a core and PB-210 approaches RA-226.

A number literal has zero uncertainty, so `=[PB-210] * 2` doubles both the value and the
1σ, while `=[PB-210] - 5` shifts the value and leaves the 1σ alone.

## How a measured column gets its number

Worth knowing, because it explains the uncertainties you see before any formula runs.

When a column lists several peaks — `PB-214@295.21; PB-214@351.92; BI-214@609.31` — Chenin
combines them with an **inverse-variance weighted mean**, which is the scientific standard
and what Génie 2000 itself reports:

```
value = Σ(wᵢ · xᵢ) / Σwᵢ      where wᵢ = 1 / σᵢ²
1σ    = √(1 / Σwᵢ)
```

The more precise a line is, the more it counts. The combined uncertainty is smaller than
any single line's — the opposite of what subtraction does.

Peaks with no value, no uncertainty, or a zero uncertainty are silently skipped. If every
peak is unusable the column is blank for that sample. A column with a single peak just
returns that peak.

### Matching a peak to a spectrum line

`PB-210@46.54` means: in section 3 of the report, find rows whose nuclide is exactly
`PB-210`, then take the one whose energy is **closest to 46.54 keV, within 1.0 keV**.

The tolerance is why `46.5` and `46.54` both work. It is also why a mistyped energy can
silently match a *neighbouring* line rather than failing loudly — if two lines of the same
nuclide sit within 1 keV of each other, check which one you actually got.

If no line matches, or the activity is missing, the column is blank for that sample. It is
not an error: a nuclide genuinely absent from one slice is normal.

## Blank values

A missing measurement is blank (`NaN`), and blanks propagate: if `RA-226` is blank for a
sample, `PB-Exc` is blank too. That is intentional — a partial subtraction would be a
fabricated number.

## Error messages

| Message | What happened |
|---|---|
| `invalid syntax` | The expression is not valid arithmetic — a dangling operator, an unclosed bracket, an empty formula. |
| `unknown nuclide 'x' in formula` | You referenced a column that is not a measured column. Check the spelling, and see the limitation below. |
| `column 'X' formula references unknown nuclide 'y'` | Same problem, caught when the template is loaded rather than when a row is built. |
| `operator Pow is not allowed` | You used `**` or `^`. Also appears as `BitAnd`, `Mod`, `FloorDiv` for `&`, `%`, `//`. |
| `unsupported expression element: Call` | You called a function, e.g. `sqrt(...)`. Also `Attribute`, `Subscript`, `Compare` for `a.b`, `a[0]`, `a > b`. |
| `division by zero` | The denominator evaluated to exactly zero. |

## Limitations worth knowing

**A formula cannot reference another formula.** Formulas see *measured* columns only. So
`=[PB-Exc] * 2` fails with `unknown nuclide 'pb_exc'`, even though `PB-Exc` is right there
in your table. Write out the full expression instead: `=([PB-210] - [RA-226]) * 2`.

**Scientific notation does not work.** `=[PB-210] * 1e3` fails with
`unknown nuclide 'e3'`. Write `1000`.

Both of these, and a few others, are tracked in
[known issues](https://github.com/Ezacuak/chenin/blob/main/docs/dev/known-issues.md).
