# Known issues

Confirmed rough edges, each with a reproduction. Not a wishlist — everything here has been
observed in the current code.

---

## 1. Scientific notation in formulas is rejected

**Severity:** low, but the error message is actively misleading.

```
=[PB-210] * 1e3   ->  column 'X' formula references unknown nuclide 'e3'
```

`_validate_column` in `synthesis/config.py` scans the formula for identifiers with
`[A-Za-z_][A-Za-z0-9_]*`, which matches the `e3` inside a float literal. The evaluator
itself would handle `1e3` fine — it is only the pre-validation that rejects it.

**Workaround:** write `1000`.

**Fix:** strip numeric literals before scanning for identifiers, or walk the parsed AST for
`ast.Name` nodes instead of regexing the source. The AST walk is the right answer: it
cannot disagree with what the evaluator actually resolves.

---

## 2. A formula cannot reference another formula column

**Severity:** medium — a real modelling limitation, currently documented rather than fixed.

```
=[PB-Exc] * 2   ->  column 'X' formula references unknown nuclide 'pb_exc'
```

`SynthesisBuilder._build_row` builds the formula namespace from `config.nuclides`, which
holds measured (peak) columns only. Derived columns never enter it.

**Workaround:** inline the expression — `=([PB-210] - [RA-226]) * 2`.

**Fix:** resolve columns in dependency order and add each derived result to the namespace as
it is computed. Needs a cycle check (`A = B + 1`, `B = A + 1`) and a topological sort, which
is why it has not been done casually.

---

## 3. Peak matching can silently hit the wrong line

**Severity:** medium — wrong numbers, no error.

`providers.py` matches a configured peak to the **nearest** section-3 line of the same
nuclide within `ENERGY_TOLERANCE = 1.0` keV. Where two lines of one nuclide sit within
1 keV of each other, a mistyped energy resolves to the neighbour instead of failing.

**Fix options:** warn when a second candidate line falls inside the tolerance; or record the
matched energy in the build result so it can be checked afterwards. The second is cheaper
and useful anyway — the Core canvas design already shows raw section 3 for exactly this
reason.

---

## 4. `ZeroDivisionError` escapes `Measurement.__truediv__`

**Severity:** low — fixed at the two known call sites, not at the source.

`measurement.py` guards the relative-uncertainty term with `_safe_div` but divides raw
floats for the value, so `a / b` with `b.value == 0.0` raises.

```python
Measurement(1.0, 0.1) / Measurement(0.0, 0.1)   # ZeroDivisionError
```

The Synthesis page's `_validate_formula` and the doc formula tester now catch it. Anything
else evaluating a user-written formula must remember to, which is the smell.

**Fix:** decide what `x / 0` means for a measurement. Returning `Measurement.missing()` is
consistent with how every other missing value behaves and would remove the trap entirely.

---

## 5. SERAC export is unreachable from the UI

**Severity:** medium — a finished feature nobody can use.

`serac.py::export_serac` is complete: mm depth conversion, column mapping, dropping
unmeasured rows, a clear error when a required column is missing. `components/export.py`
supports a `"SERAC"` format. But **no page passes `formats=(..., "SERAC")`**, so the option
never appears, even though the Home page advertises SERAC export.

**Fix:** pass the format from the Synthesis page's preview panel. Blocked on nothing except
deciding which of the five builder designs owns the export button. Note it also needs `DBD`
filled in, so it should be disabled with an explanation when that column is empty.

Related: `serac.py` has **no tests**.

---

## 6. `g2k_parser` has no tests

**Severity:** medium — it is the layer most likely to break, and the least covered.

The 42-test suite covers `synthesis/` only. Parsing is exercised end to end by two
`requires_data` tests and nothing else, so a regression in a section regex shows up as a
wrong number rather than a red test.

**Fix:** a fixture report per section — small hand-written excerpts, not whole files — plus
a golden-frame test per `extract_s*`. The `_require` failure path deserves a test each too.

---

## 7. Section identity is positional

**Severity:** low probability, high impact.

`parser.py` indexes sections by position among the banner blocks. A report with a missing or
extra banner shifts everything after it, and each section's `_require` check will usually
then fail — but on an unlucky layout it could pass and produce a misattributed frame.

**Fix:** match sections by normalised banner title with a positional fallback.

---

## 8. Documentation that outlives its subject

Not a code issue, but worth recording: `CLAUDE.md` and `AGENTS.md` are gitignored, so
anything written only there is invisible to anyone who clones the repo. Both described
`serac.py` as "a placeholder returning dummy bytes" for some time after it was fully
implemented.

Durable facts belong in `docs/`. The agent files should hold pointers, not truth.
