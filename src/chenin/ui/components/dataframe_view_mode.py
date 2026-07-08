from enum import Enum

import pandas as pd
import streamlit as st
from streamlit_extras.dataframe_explorer import dataframe_explorer

_AGGREGATIONS = ("mean", "sum", "count", "min", "max", "median")


class DfViewMode(Enum):
    TABLE = "Table"
    PIVOT = "Pivot"
    FILTERED = "Filter"


def _pivot_view(df: pd.DataFrame, key: str) -> None:
    """A native pivot builder: pick row fields, value fields and an aggregation."""
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if not numeric_cols:
        st.caption("No numeric columns to aggregate.")
        return

    left, mid, right = st.columns(3)
    rows = left.multiselect("Rows", list(df.columns), key=f"pivot_rows_{key}")
    values = mid.multiselect(
        "Values", numeric_cols, default=numeric_cols[:1], key=f"pivot_values_{key}"
    )
    aggfunc = right.selectbox("Aggregation", _AGGREGATIONS, key=f"pivot_agg_{key}")

    if not rows or not values:
        st.caption("Pick at least one **Rows** field and one **Values** field.")
        return

    table = pd.pivot_table(df, index=rows, values=values, aggfunc=aggfunc)
    st.dataframe(table, width="stretch")


def df_view_mode_widget(df: pd.DataFrame, name: str, key: str) -> None:
    """Row/column count caption + a Table/Pivot/Filter toggle for a dataframe."""
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

    if view == DfViewMode.PIVOT:
        _pivot_view(df, key=f"{name}_{key}")
    elif view == DfViewMode.FILTERED:
        st.dataframe(dataframe_explorer(df), hide_index=True, width="stretch")
    else:
        st.dataframe(df, hide_index=True, width="stretch")
