import tempfile
from pathlib import Path

import streamlit as st

from g2k_parser import SECTION_DESCRIPTIONS
from report import Report

st.title("Chenin")
st.markdown("A tool to extract data from `Génie200` report.")

with st.sidebar:
    st.header("Open reports")
    uploaded_files = st.file_uploader(
        "Select one or more G2K report files",
        type=["txt", "pdf"],
        accept_multiple_files=True,
    )

if not uploaded_files:
    st.info("Upload one or more G2K report files in the sidebar to get started.")
    st.stop()

tabs = st.tabs([f.name for f in uploaded_files])

for tab, uploaded_file in zip(tabs, uploaded_files):
    with tab:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(uploaded_file.name).suffix
        ) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        try:
            report = Report(tmp_path)
        except Exception as exc:
            st.error(f"Failed to parse {uploaded_file.name}: {exc}")
            continue

        st.header("Sections")

        for key in report:
            with st.container(border=True):
                st.subheader(SECTION_DESCRIPTIONS[key])
                st.dataframe(report[key])
