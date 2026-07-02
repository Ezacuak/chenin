import pandas as pd
import state
import streamlit as st
from components.export import export_dataframe
from streamlit_extras.dataframe_explorer import *
from streamlit_pivot import st_pivot_table

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

_TABLE = "Tableau"
_PIVOT = "Pivot"
_FILTERED = "Filtre"

for tab, (name, report) in zip(tabs, reports.items()):
    with tab:
        st.subheader("Sections", divider="gray")

        for key in report:
            df = report[key]

            with st.container(border=True):
                st.markdown(f"##### {SECTION_DESCRIPTIONS[key]}")

                with st.container(
                    horizontal=True,
                    horizontal_alignment="distribute",
                    vertical_alignment="center",
                ):
                    st.caption(
                        f":material/table_rows: {len(df)} lignes "
                        f"· :material/view_column: {len(df.columns)} colonnes"
                    )

                    view = st.segmented_control(
                        "Affichage",
                        [_TABLE, _PIVOT, _FILTERED],
                        default=_TABLE,
                        key=f"view_{name}_{key}",
                        label_visibility="collapsed",
                        width="content",
                    )

                if view == _PIVOT:
                    st_pivot_table(df, key=f"pivot_{name}_{key}")
                elif view == _FILTERED:
                    df = dataframe_explorer(df)
                    st.dataframe(df)
                else:
                    st.dataframe(df, hide_index=True)

                export_dataframe(df, filename=f"{name}-{key}")
