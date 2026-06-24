import state
import streamlit as st
from components.export import export_widget

from g2k_parser import SECTION_DESCRIPTIONS

st.title("Extraction de rapport")

with st.sidebar:
    st.header("Ouvrir des rapports")
    reports_files = st.file_uploader(
        "Sélectionner un ou plusieurs fichiers de rapport G2K",
        type=["txt", "pdf"],
        accept_multiple_files=True,
    )

state.store_reports(reports_files)

reports = state.get_reports()

if not reports:
    st.info(
        "Chargez un ou plusieurs fichiers de rapport G2K dans la barre latérale pour commencer."
    )
    st.stop()

tabs = st.tabs(list(reports.keys()))

for tab, (name, report) in zip(tabs, reports.items()):
    with tab:
        st.header("Sections")

        for key in report:
            with st.container(border=True):
                st.subheader(SECTION_DESCRIPTIONS[key])
                df = report[key]
                st.dataframe(df)
                export_widget(df, filename=f"{name}-{key}")
