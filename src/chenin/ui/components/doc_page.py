"""Locate, read and render the user guide (``docs/guide/*.md``).

The markdown files are the single source of truth: browsable on GitHub under
``docs/guide/`` and force-included into the wheel at ``chenin/docs/guide`` (see
``pyproject.toml``). Every page under ``app_pages/docs/`` is a two-line stub calling
:func:`render_doc`.
"""

from functools import lru_cache
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path

import streamlit as st

_GUIDE = ("docs", "guide")


@lru_cache(maxsize=1)
def guide_root() -> Traversable:
    """The directory holding the user-guide markdown files.

    Two layouts must both work:

    * **source checkout / editable install** — ``chenin`` resolves to ``<repo>/src/chenin``
      through the ``.pth`` file, so the live files sit at ``<repo>/docs/guide``. This is
      tried first: hatchling copies the forced includes into ``site-packages`` even for
      an editable install, and that copy goes stale the moment a doc is edited.
    * **installed wheel** — the files were force-included at ``chenin/docs/guide``.
    """
    package = resources.files("chenin")

    if isinstance(package, Path):
        repo_root = package.parents[1]  # <repo>/src/chenin -> <repo>
        checkout = repo_root.joinpath(*_GUIDE)
        if (repo_root / "pyproject.toml").is_file() and checkout.is_dir():
            return checkout

    return package.joinpath(*_GUIDE)


def read_doc(name: str) -> str:
    """Read one guide file, e.g. ``read_doc("formulas.md")``."""
    return guide_root().joinpath(name).read_text(encoding="utf-8")


def render_doc(name: str) -> None:
    """Render one guide file as the body of a page.

    A leading ``# Heading`` becomes :func:`st.title`, so the app gets a real title
    element while the file still opens on GitHub with a proper H1 — written once.
    """
    try:
        body = read_doc(name)
    except OSError as exc:
        st.error(f"Documentation file `{name}` is missing from this installation ({exc}).")
        return

    title, rest = _split_title(body)
    if title:
        st.title(title)
    st.markdown(rest, unsafe_allow_html=False)


def _split_title(body: str) -> tuple[str, str]:
    head, _, rest = body.partition("\n")
    if head.startswith("# "):
        return head[2:].strip(), rest.lstrip("\n")
    return "", body
