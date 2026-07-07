import pandas as pd
import streamlit as st

from g2k_parser import Report
from synthesis import BuildConfig

BUILD_CONFIG_KEY = "build_config"
REPORTS_KEY = "reports"
SYNTHESIS_KEY = "synthesis"


def store_build(config: BuildConfig, reports: dict[str, Report]) -> None:
    """Store the build configuration and its loaded reports (posed by app.py)."""
    st.session_state[BUILD_CONFIG_KEY] = config
    st.session_state[REPORTS_KEY] = reports


def get_build_config() -> BuildConfig | None:
    return st.session_state.get(BUILD_CONFIG_KEY)


def get_reports() -> dict[str, Report]:
    stored = st.session_state.get(REPORTS_KEY)
    if stored is None:
        return {}
    return stored


def store_synthesis(df: pd.DataFrame) -> None:
    st.session_state[SYNTHESIS_KEY] = df


def get_synthesis() -> pd.DataFrame | None:
    return st.session_state.get(SYNTHESIS_KEY)
