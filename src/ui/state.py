import hashlib
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from g2k_parser import Report

REPORTS_KEY = "report_files"
SYNTHESIS_KEY = "synthesis"
SYNTHESIS_ORDER_KEY = "synthesis_order"


@st.cache_resource(hash_funcs={bytes: hashlib.md5})
def _parse(suffix: str, data: bytes) -> Report:
    """Parse uploaded bytes into a ``Report`` (cached on the file content)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
    return Report(tmp.name)


def store_uploaded(uploaded_files) -> None:
    """Persist uploaded file bytes in session state (called from the upload page)."""
    if uploaded_files:
        st.session_state[REPORTS_KEY] = {
            f.name: {"suffix": Path(f.name).suffix, "data": f.read()}
            for f in uploaded_files
        }


def get_reports() -> tuple[dict[str, Report], dict[str, str]]:
    """Parse every stored report.

    Returns ``(reports_by_name, errors_by_name)`` so pages can render parse
    failures uniformly without crashing on a single bad file.
    """
    reports: dict[str, Report] = {}
    errors: dict[str, str] = {}
    for name, meta in st.session_state.get(REPORTS_KEY, {}).items():
        try:
            reports[name] = _parse(meta["suffix"], meta["data"])
        except Exception as exc:  # noqa: BLE001 - surfaced to the user in the UI
            errors[name] = str(exc)
    return reports, errors


def store_synthesis(df: pd.DataFrame) -> None:
    """Persist the built synthesis and the ``numero -> report name`` mapping.

    The order map lets the core-visualization page link a slice back to the
    G2K report it was built from.
    """
    st.session_state[SYNTHESIS_KEY] = df


def get_synthesis() -> pd.DataFrame | None:
    return st.session_state.get(SYNTHESIS_KEY)
