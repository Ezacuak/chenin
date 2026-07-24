from enum import Enum

import pandas as pd
import streamlit as st
from streamlit_extras.dataframe_explorer import dataframe_explorer
from streamlit_pivot import st_pivot_table


class DfViewMode(Enum):
    TABLE = "Table"
    PIVOT = "Pivot"
    FILTERED = "Filter"


def df_view_mode_widget(df: pd.DataFrame, name: str, key: str) -> pd.DataFrame:
    """Row/column count caption + a Table/Pivot/Filter toggle for a dataframe.

    Returns the dataframe currently on screen (filtered or pivoted when those views are
    active) so the caller can export exactly what the user sees.
    """
    with st.container(
        horizontal=True,
        horizontal_alignment="distribute",
        vertical_alignment="center",
    ):
        st.caption(
            f":material/table_rows: {len(df)} rows "
            f"· :material/view_column: {len(df.columns)} columns"
        )

        view = st.segmented_control(
            "Display",
            list(DfViewMode),
            format_func=lambda mode: mode.value,
            default=DfViewMode.TABLE,
            key=f"view_{name}_{key}",
            label_visibility="collapsed",
            width="content",
        )

    match view:
        case DfViewMode.TABLE:
            st.dataframe(df, hide_index=True, width="stretch")
            return df

        case DfViewMode.PIVOT:
            result = st_pivot_table(df, key=f"{name}_{key}")
            st.dataframe(result)
            return df

        case DfViewMode.FILTERED:
            filtered = dataframe_explorer(df)
            st.dataframe(filtered, hide_index=True, width="stretch")
            return filtered

        case _:
            st.dataframe(df, hide_index=True, width="stretch")
            return df
