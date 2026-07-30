# Formula Tester

A scratchpad for derived columns. Edit the activities below, type a formula, and see the
result and its propagated uncertainty immediately.

This runs the **real evaluator** — the same code that builds your synthesis — so anything
that works here works in a template, and any error you see here is the error you would get
at build time. Nothing on this page touches your loaded reports or your synthesis.

The syntax reference is on the
[Formulas](https://github.com/Ezacuak/chenin/blob/main/docs/guide/formulas.md) page. Things
worth trying:

- `=[PB-210] - [RA-226]` — excess ²¹⁰Pb, the standard case.
- `=[PB-210] / [RA-226]` — a ratio, to see how relative uncertainties combine.
- `=([PB-210] - [RA-226]) * 2` — parentheses and a constant.
- `=[PB-210] ** 2` — rejected, to see what a refused operator looks like.
