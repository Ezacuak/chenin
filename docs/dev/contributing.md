# Contributing

## Setup

```sh
git clone https://github.com/Ezacuak/chenin.git
cd chenin
uv sync
```

Requires Python ≥ 3.14, which uv installs for you if you do not have it. `uv sync` builds
`.venv/` from the committed `uv.lock`, so everyone gets identical versions.

## The commands

```sh
uv run pytest                       # the test suite
uv run pytest tests/test_config.py  # one file
uvx ruff check src/ tests/          # lint (line-length 100)
uvx ruff check --fix src/ tests/    # autofix what it can
uv run chenin app                   # the app, against your working tree
uv run chenin extract data/NOIR24-01/NOI_S_1.txt -s s3
```

Run `ruff` and `pytest` before every commit. There is no CI to catch it for you.

## uv, in practice

| Task | Command |
|---|---|
| Install everything from the lockfile | `uv sync` |
| Add a runtime dependency | `uv add plotly` |
| Add a dev-only dependency | `uv add --dev pytest-cov` |
| Remove one | `uv remove plotly` |
| Update the lockfile | `uv lock --upgrade` |
| Verify the lockfile is current | `uv lock --check` |
| Run a tool without installing it | `uvx ruff check src/` |

`uv add`/`uv remove` edit `pyproject.toml` **and** `uv.lock`. Commit both together — a
lockfile out of step with the manifest breaks `uv sync --locked`, which is what the Docker
build uses.

Dev dependencies live in `[dependency-groups] dev` and are excluded from the wheel and from
`uv sync --no-dev`.

## Tests

`testpaths = ["tests"]`, so only `tests/` is collected. Note `test.py` at the repo root is
a UI design scratchpad, not a test, and is deliberately not collected.

Tests that need the real core are gated on a `requires_data` skipif marker pointing at
`data/NOIR24-01/` — they skip cleanly if the data is absent.

`tests/conftest.py` provides an `s3` fixture (two `PB-214` lines and one `CS-137`, with
hand-checkable inverse-variance weights) and a `FakeReport` stub exposing just
`report["s3"]` and `.name`. Prefer those over building a real `Report` when what you are
testing is synthesis logic.

## Documentation

Markdown in `docs/` is the single source of truth. `docs/guide/` is the user guide —
browsable on GitHub, force-included into the wheel, and rendered in the app's sidebar.
`docs/dev/` is repo-only and is not shipped.

### Adding a guide page

1. Write `docs/guide/my-page.md`, starting with a single `# Title` line.
2. Add a two-line stub at `src/chenin/ui/app_pages/docs/my-page.py`:

   ```python
   from chenin.ui.components.doc_page import render_doc

   render_doc("my-page.md")
   ```

3. Register it in the `"Documentation"` section of `src/chenin/ui/app.py`.
4. Add a row to `docs/README.md`.

The stub's filename becomes the page's URL path, so it must not collide with `home`,
`data_loader`, `reports` or `synthesis` — `st.navigation` raises on duplicate paths.
Icon names are validated at import: an unknown `:material/…` name raises immediately.

`tests/test_docs.py` asserts every stub's target file exists, so a rename fails in pytest
rather than in the sidebar.

### House style

The same file is read on GitHub and rendered by `st.markdown`, so it must be portable:

- **Pipe tables are fine** — Streamlit renders GFM tables.
- **No raw HTML.** It is rendered with `unsafe_allow_html=False` and will be stripped.
- **No `:material/…` shortcodes** in markdown. They render in the app and appear as literal
  text on GitHub.
- **Cross-page links from `docs/guide/` must be absolute** `https://github.com/...` URLs.
  Relative paths work on GitHub and 404 in the app. `docs/dev/` is GitHub-only, so relative
  links are fine there.
- **No images with relative paths** — use `raw.githubusercontent.com` URLs, or call
  `st.image()` in the stub after `render_doc`.

### How the files reach an installed wheel

`pyproject.toml` force-includes `docs/guide` at `chenin/docs/guide`. `doc_page.guide_root()`
prefers the **source checkout** when one is detectable, because hatchling also copies forced
includes into `site-packages` for editable installs and that copy goes stale as soon as you
edit a `.md`. If a doc edit is not showing up, that fallback order is the thing to check.

Only `docs/guide` is force-included — hatchling's `exclude` does not apply to forced
includes, so listing `docs/` would ship the dev docs too.

## Conventions worth not breaking

- **Column names are constants** in `g2k_parser/columns.py`. Import them; do not retype the
  string.
- **Synthesis output columns are French** (`Echantillon`, `Profondeur`, `Activite …`). They
  feed SERAC and the lab's workbooks. The UI and docs are English; the data columns are not.
- **Geometry is a column kind**, not a prefix rule. Exactly one of `source`, `formula`,
  `geometry` is set on a `ColumnSpec`, and `BuildConfig` enforces it.
- **Pages go through `state.py`** rather than touching `st.session_state` directly.
- **Line length 100**, ruff rules `E, F, W, I, UP, B, SIM`.
- **CSV output** goes to `out/` (gitignored). Data CSVs are gitignored.

## Adding a column kind

`ColumnSpec` allows exactly one of `source`, `formula` and `geometry`. A fourth kind means
touching, in order: the dataclass, `_validate_column` in `config.py`, the write branch in
`SynthesisBuilder._build_row`, `_schema_to_specs` in the Synthesis page, and
`docs/guide/synthesis-template.md`. Check first whether a formula would do the job.
