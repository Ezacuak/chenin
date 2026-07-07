import pandas as pd
import state
import streamlit as st
from components.dataframe_view_mode import df_view_mode_widget
from components.export import export_dataframe

from g2k_parser import SECTION_DESCRIPTIONS

pd.set_option("display.float_format", lambda x: f"{x:f}")

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
        st.subheader("Sections", divider="gray")

        for key in report:
            df = report[key]

            with st.container(border=True):
                st.markdown(f"##### {SECTION_DESCRIPTIONS[key]}")

                df_view_mode_widget(df, name, key)

                export_dataframe(df, filename=f"{name}-{key}")
