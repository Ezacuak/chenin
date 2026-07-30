# Deliberately plain Dockerfile syntax: no cache or bind mounts, so this builds on the
# legacy builder as well as BuildKit/buildx. Layer caching comes from COPY ordering.

# ---------------------------------------------------------------------------
# Build stage: resolve and install into a self-contained /app/.venv
# ---------------------------------------------------------------------------
FROM python:3.14-slim AS build

# Pinned so image builds are reproducible; bump alongside uv.lock.
COPY --from=ghcr.io/astral-sh/uv:0.11.2 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependencies first: this layer is invalidated only by pyproject.toml / uv.lock.
# README.md is copied too because pyproject declares `readme = "README.md"`, which uv
# reads even when it is not installing the project itself.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project

# Then the project. docs/ must be in the build context: pyproject force-includes
# docs/guide into the wheel and hatchling aborts with "Forced include not found"
# if the directory is absent.
COPY src ./src
COPY docs ./docs

# --no-editable installs a real copy into the venv, so the runtime stage needs
# nothing but the venv — and the packaged docs get exercised for real.
RUN uv sync --locked --no-dev --no-editable

# ---------------------------------------------------------------------------
# Runtime stage
# ---------------------------------------------------------------------------
FROM python:3.14-slim AS runtime

LABEL org.opencontainers.image.title="chenin" \
      org.opencontainers.image.description="Génie 2000 report extraction and sediment-core synthesis" \
      org.opencontainers.image.source="https://github.com/Ezacuak/chenin"

RUN useradd --create-home --uid 10001 chenin

# `chenin app` shells out to `streamlit run` without an address or headless flag, so
# they are supplied here instead: Streamlit maps STREAMLIT_<SECTION>_<KEY> onto config.
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/home/chenin \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# The venv keeps its absolute /app/.venv path so console-script shebangs stay valid.
COPY --from=build --chown=chenin:chenin /app/.venv /app/.venv

USER chenin
WORKDIR /home/chenin

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3).status == 200 else 1)"

CMD ["chenin", "app", "--port", "8501"]
