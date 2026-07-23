"""Shared Streamlit session-state helpers, used by app.py and every page."""

import pandas as pd
import streamlit as st

from chenin.g2k_parser import Report

REPORTS_KEY = "reports"
SYNTHESIS_KEY = "synthesis"


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
