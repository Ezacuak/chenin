"""Shared Streamlit session-state helpers, used by app.py and every page."""

import pandas as pd
import streamlit as st

from chenin.g2k_parser import Report

REPORTS_KEY = "reports"
SYNTHESIS_KEY = "synthesis"
NUCLIDE_LIBRARY_KEY = "nuclide_library"

# Reference peaks for common nuclides, editable from the Synthesis page.
DEFAULT_NUCLIDE_LIBRARY: dict[str, list[float]] = {
    "CO-60": [1173.2, 1332.5],
    "CS-137": [661.7],
    "NA-22": [511.0, 1274.5],
    "PB-210": [46.5],
    "RA-226": [186.2],
    "K-40": [1460.8],
    "AM-241": [59.5],
}


def store_reports(reports: dict[str, Report]) -> None:
    st.session_state[REPORTS_KEY] = reports


def get_reports() -> dict[str, Report]:
    stored = st.session_state.get(REPORTS_KEY)
    if stored is None:
        return {}
    return stored


def store_synthesis(df: pd.DataFrame) -> None:
    st.session_state[SYNTHESIS_KEY] = df


def get_synthesis() -> pd.DataFrame | None:
    return st.session_state.get(SYNTHESIS_KEY)


def store_nuclide_library(library: dict[str, list[float]]) -> None:
    st.session_state[NUCLIDE_LIBRARY_KEY] = library


def get_nuclide_library() -> dict[str, list[float]]:
    stored = st.session_state.get(NUCLIDE_LIBRARY_KEY)
    if stored is None:
        stored = DEFAULT_NUCLIDE_LIBRARY.copy()
        st.session_state[NUCLIDE_LIBRARY_KEY] = stored
    return stored
