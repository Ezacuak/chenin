import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from g2k_parser import Report

REPORTS_KEY = "reports"
SYNTHESIS_KEY = "synthesis"


def store_reports(files) -> None:
    reports = get_reports()

    for file in files:
        name = Path(file.name).stem
        if name in reports:
            continue

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name
        print(tmp_path)
        report = Report(tmp_path)
        Path(tmp_path).unlink()
        reports[name] = report

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
