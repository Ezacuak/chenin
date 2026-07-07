from enum import Enum

import pandas as pd
import streamlit as st
from streamlit_extras.dataframe_explorer import dataframe_explorer
from streamlit_pivot import st_pivot_table


class DF_VIEW_MODE(Enum):
    TABLE = "Tableau"
    PIVOT = "Pivot"
    FILTERED = "Filtre"


def df_view_mode_widget(df: pd.DataFrame, name: str, key: str):
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
        list(DF_VIEW_MODE),
        format_func=lambda mode: mode.value,
        default=DF_VIEW_MODE.TABLE,
        key=f"view_{name}_{key}",
        label_visibility="collapsed",
        width="content",
    )

    if view == DF_VIEW_MODE.PIVOT:
        st_pivot_table(df, key=f"pivot_{name}_{key}")
    elif view == DF_VIEW_MODE.FILTERED:
        df = dataframe_explorer(df)
        st.dataframe(df)
    else:
        st.dataframe(df, hide_index=True)
