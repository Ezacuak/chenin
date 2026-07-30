# Deploy

Three ways Chenin reaches its users, in order of how often they are used.

## 1. Lab machines — `uv tool install`

This is the normal path. Each person installs the tool on their own machine and runs the
app locally; there is no server to maintain and no data leaves the laptop.

The end-user instructions are
[Install & Update](../guide/install.md) — send people there rather than
retyping the commands. In short:

```sh
uv tool install git+https://github.com/Ezacuak/chenin.git
chenin app
```

To put people on an unreleased branch:

```sh
uv tool install git+https://github.com/Ezacuak/chenin.git@dev
```

`uv tool install` builds from the checkout, so `docs/guide` and
`synthesis/default_template.csv` are packaged the same way as in a wheel — no extra step.

### Windows notes

uv installs via PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

The installer edits `PATH`; **a terminal opened before that still has the old one**. Almost
every "command not found" report is this. Tell people to open a new terminal.

Git must also be installed, because `uv` shells out to the `git` CLI to fetch a `git+`
dependency: [git-scm.com/download/win](https://git-scm.com/download/win).

## 2. Docker

For a lab server, or to hand someone a running app without installing anything.

```sh
docker build -t chenin:0.2.0 -t chenin:latest .
docker run --rm -p 8501:8501 chenin:0.2.0
```

The app is then on `http://localhost:8501`, or on the server's address for anyone who can
reach it.

To make a folder of reports available to the container:

```sh
docker run --rm -p 8501:8501 -v "$PWD/data:/data:ro" chenin:0.2.0
```

### How the image is put together

Two stages. The build stage uses a pinned `uv` and installs from `uv.lock` with
`--locked`, so an image build fails loudly rather than silently resolving different
versions. Dependencies install in their own layer (`--no-install-project`) so editing the
source does not re-download pandas. The runtime stage copies only `/app/.venv`, at its
original path so the console-script shebangs stay valid, and runs as a non-root user.

Three things that will bite you if you change it:

- **`docs/` must be in the build context.** `pyproject.toml` force-includes `docs/guide`,
  and hatchling aborts with `Forced include not found` if it is missing. `.dockerignore`
  says so in a comment; keep it.
- **`--server.address` and `--server.headless` are set as environment variables**, not
  flags. `chenin app` hardcodes only `--server.port`, so a container that does not set
  `STREAMLIT_SERVER_ADDRESS=0.0.0.0` binds to localhost inside the container and is
  unreachable from outside. Using the env vars keeps `CMD` on the project's real entry
  point instead of hardcoding a path into site-packages.
- **`uv.lock` must match `pyproject.toml`.** `--locked` is the point; do not relax it.

The theme in `.streamlit/config.toml.back` is **not** copied in — it is disabled in the
repo too. If you enable it, add a `COPY` for it into `/home/chenin/.streamlit/config.toml`.

The healthcheck hits Streamlit's `/_stcore/health`.

### What is not here

No `docker-compose.yml`, no reverse-proxy config, no TLS, and **no authentication** — the
app has no concept of users. Do not expose the port to a public network as-is; put it
behind the lab's existing auth, or keep it on a private network.

## 3. Cutting a release

There is no CI and no PyPI publication. A release is a version bump and a tag.

1. Make sure `main` is green: `uvx ruff check src/ tests/ && uv run pytest`.
2. Bump `version` in `pyproject.toml` (semver: breaking / feature / fix).
3. Update `uv.lock` if dependencies moved: `uv lock` — commit both files together.
4. Commit, tag, push:

   ```sh
   git commit -am "release: 0.3.0"
   git tag -a v0.3.0 -m "0.3.0"
   git push origin main --tags
   ```

5. Tell users to upgrade:

   ```sh
   uv tool upgrade chenin
   ```

   Anyone who installed from a branch should re-run the install command with the same
   `@branch` suffix — `upgrade` follows whatever they originally asked for.

Because installs come from git, **whatever is on `main` is what new users get**, tag or no
tag. The tag is for being able to say which version someone is running; `main` is the
actual release channel. Do not merge to `main` mid-refactor.

### Verifying a build before tagging

```sh
uv build
python -m zipfile -l dist/chenin-0.3.0-py3-none-any.whl | grep docs
```

`chenin/docs/guide/*.md` should be listed and `docs/dev/` should not. If the guide is
missing, the app's Documentation pages will render an error for every page on a fresh
install — and you will not see it locally, because the source checkout takes priority.
