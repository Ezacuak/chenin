"""Shared Streamlit session-state helpers, used by app.py and every page."""

import pandas as pd
import streamlit as st

from chenin.g2k_parser import Report

REPORTS_KEY = "reports"
SYNTHESIS_KEY = "synthesis"
NUCLIDE_LIBRARY_KEY = "nuclide_library"
LAYERS_KEY = "layers"

DEFAULT_NUCLIDE_LIBRARY: dict[str, list[float]] = {
    "CS-137": [661.7],
    "PB-210": [46.5],
    "Th-228": [238.6],
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


def store_layers(layers: pd.DataFrame) -> None:
    """Store the core-layer table (one row per report: depths, density, sample code).

    G2K reports carry no depth, so this is the one place the layer geometry exists.
    Every builder concept reads it from here.
    """
    st.session_state[LAYERS_KEY] = layers


def get_layers() -> pd.DataFrame | None:
    return st.session_state.get(LAYERS_KEY)


def store_nuclide_library(library: dict[str, list[float]]) -> None:
    st.session_state[NUCLIDE_LIBRARY_KEY] = library


def get_nuclide_library() -> dict[str, list[float]]:
    stored = st.session_state.get(NUCLIDE_LIBRARY_KEY)
    if stored is None:
        stored = DEFAULT_NUCLIDE_LIBRARY.copy()
        st.session_state[NUCLIDE_LIBRARY_KEY] = stored
    return stored
