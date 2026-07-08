# Commit plan — « Big Build File » refactor

Branch: `build_file` (off `main`). The change is one feature (single build file drives everything)
split into 6 review-scoped commits. Conventional-commit style matches the repo
(`feat(scope):`, `fix(scope):`).

**Green checkpoints** — the `BuildConfig` rename couples several files, so intermediate snapshots
aren't all runnable:
- After **commit 1**: library imports + `pytest` pass. CLI stays as-was (already broken on `main`).
- After **commit 2**: CLI (`synthesis` / `extract`) works end-to-end.
- After **commit 4**: Streamlit app imports cleanly and renders (the app-level `SynthesisConfig`
  reference is replaced during the UI rework).
- Branch tip: everything green (pytest, CLI, Streamlit, ruff).

Note: the old `data/NOI_S/NOI_S_Synthesis.toml` is gitignored (data dir) — its deletion is not a
git change and needs no commit.

---

## Commit 1 — feat(synthesis): model samples + depths in a unified BuildConfig

**Files**
- `src/synthesis/config.py` — add `SampleSpec`; rename `SynthesisConfig` → `BuildConfig` (+ `base_path`, `samples`); drop `MetadataSpec.epaisseur`; add `_parse_sample` validation.
- `src/synthesis/loader.py` *(new)* — `load_reports(config, base_dir)` reads each sample under `base_path`.
- `src/synthesis/builder.py` — `build(reports: dict)` iterates `config.samples`; `Profondeur=depth_top`, `Epaisseur=depth_bot-depth_top`, `Age` from `depth_top`; remove cumulative-depth logic and dead `_NUMERO_RE`.
- `src/synthesis/__init__.py`, `src/__init__.py` — export `BuildConfig`, `SampleSpec`, `load_reports`.
- `tests/test_synthesis.py` *(new)*, `pyproject.toml` — pytest suite + `pythonpath`/`testpaths` config.

**Message**
```
feat(synthesis): model samples + depths in a unified BuildConfig

Sample geometry (depth_top/depth_bot) is absent from G2K reports and had
to come from somewhere. Introduce SampleSpec and fold an ordered sample
list plus base_path into the config, renamed SynthesisConfig -> BuildConfig
to reflect that one file now describes the whole build.

The builder emits one row per sample in build-file order: Profondeur is
depth_top, Epaisseur is derived (depth_bot - depth_top), and Age uses
depth_top instead of a cumulated constant thickness. load_reports() reads
each report from disk under base_path. Drops the unused epaisseur metadata
and the dead _NUMERO_RE regex.

Adds a pytest suite covering Measurement propagation, config validation,
and the per-sample builder.

BREAKING CHANGE: SynthesisConfig is renamed to BuildConfig and
MetadataSpec.epaisseur is removed (epaisseur is now per-sample).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

---

## Commit 2 — fix(cli): drive synthesis from a single build file

**Files**
- `src/cli.py` — `synthesis` subcommand takes one `build_file` (reports come from it via `load_reports`); fix `Report(path)` → `Report(path, path)` in `extract`.
- `src/main.py` — dev entry uses the build file + `load_reports`.

**Message**
```
fix(cli): drive synthesis from a single build file

`chenin synthesis BUILD_FILE.toml` now sources its reports from the build
file's [[samples]] + base_path, so they no longer have to be listed on the
command line. Also fixes the extract handler calling Report() with a single
path against its two-arg (local_path, temp_path) signature.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

---

## Commit 3 — feat(ui): single global build-file import with shared state

**Files**
- `src/app.py` — build-file uploader at the top of the sidebar; parse + `load_reports` + `state.store_build`.
- `src/ui/state.py` — `store_build`/`get_build_config`; reports read from shared state.
- `src/ui/pages/report_page.py` — drop the per-page uploader; consume `state.get_reports()`.

**Message**
```
feat(ui): single global build-file import with shared state

Move report loading to one build-file uploader at the top of the sidebar
(app.py). Both pages now consume the shared session state instead of each
owning a file uploader, giving a single point of entry for the whole app.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

---

## Commit 4 — feat(ui): synthesis core view + synthesis-scoped SERAC export

**Files**
- `src/ui/pages/synthesis_page.py` — consume shared config/reports; add a Plotly "carotte" (layer-by-layer) view + depth profiles before the table.
- `src/ui/components/export.py` — `export_dataframe(..., formats=...)`; SERAC only where requested.

**Message**
```
feat(ui): synthesis core view + synthesis-scoped SERAC export

The synthesis page reads the shared BuildConfig/reports and renders a
sediment-core view: layers coloured by a chosen activity, per-nuclide
depth profiles with error bars, then the table. SERAC export is now opt-in
via export_dataframe(formats=...) so it appears only for the synthesis,
not for raw report sections.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

---

## Commit 5 — feat(build): unified NOI_S build file

**Files**
- `NOI_S_Builder.toml` — [[samples]] (with placeholder 0.5 cm depths) + metadata + nuclides + columns.

**Message**
```
feat(build): unified NOI_S build file

Single TOML referencing every NOI_S report with its layer depths plus the
synthesis format (nuclides + columns), replacing the separate synthesis
config. Sample depths are placeholder 0.5 cm slices pending real field
values.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

---

## Commit 6 — docs: build-file schema + Measurement guide

**Files**
- `docs/synthesis.md` — rewritten for the build-file schema ([[samples]], base_path, depth_top, derived epaisseur); drop stale `Numero Echantillon`.
- `docs/measurement.md` *(new)* — what `Measurement` is, why uncertainty propagation matters, and why it stays.

**Message**
```
docs: build-file schema + Measurement guide

Update the synthesis doc to the unified build-file format and add a guide
explaining the Measurement value object (quadrature propagation and
inverse-variance weighted mean).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

---

## Suggested commands

```sh
git add src/synthesis/config.py src/synthesis/loader.py src/synthesis/builder.py \
        src/synthesis/__init__.py src/__init__.py tests/test_synthesis.py pyproject.toml
git commit   # message 1

git add src/cli.py src/main.py            && git commit   # message 2
git add src/app.py src/ui/state.py src/ui/pages/report_page.py && git commit   # message 3
git add src/ui/pages/synthesis_page.py src/ui/components/export.py && git commit   # message 4
git add NOI_S_Builder.toml                && git commit   # message 5
git add docs/synthesis.md docs/measurement.md && git commit   # message 6
```
