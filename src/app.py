import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from extraction import Report


@st.cache_data
def load_report(file_path: str) -> Report:
    return Report.from_file(file_path)


def show_s2_section(report: Report):
    st.header("S2 - RAPPORT ANALYSE DES PICS")

    df = report.extract_s2()

    if df.empty:
        st.warning("No S2 data found in report")
        return

    st.dataframe(df, use_container_width=True)


def show_s6_section(report: Report):
    st.header("S6 - RAPPORT LIMITES DE DETECTION (ISO 11929)")

    df = report.extract_s6()

    if df.empty:
        st.warning("No S6 data found in report")
        return

    st.dataframe(df, use_container_width=True)


def main():
    st.set_page_config(page_title="G2K Report Extractor", layout="wide")
    st.title("G2K Report Data Extractor")

    st.sidebar.title("Upload Report")
    uploaded_file = st.sidebar.file_uploader("Choose a G2K report (.txt)", type=["txt"])

    if uploaded_file is None:
        st.info("Upload a G2K report to get started")
        return

    with st.spinner("Processing report..."):
        temp_path = Path("/tmp") / uploaded_file.name
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        report = load_report(str(temp_path))

    st.sidebar.success(f"✓ Loaded: {uploaded_file.name}")

    show_s2_section(report)

    show_s6_section(report)


if __name__ == "__main__":
    main()
