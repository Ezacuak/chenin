"""Live formula tester: runs the real evaluator against an editable sample row."""

import pandas as pd
import streamlit as st

from chenin.synthesis import BuildConfig
from chenin.synthesis.config import expand_formula_refs
from chenin.synthesis.measurement import Measurement
from chenin.synthesis.providers import evaluate_formula
from chenin.ui.components.doc_page import render_doc

render_doc("formula-tester.md")

# Plausible mid-core activities in mBq/g with 1-sigma uncertainties. Keys come from the
# packaged default template so the tester cannot drift away from what ships; anything
# not listed falls back, which keeps the page alive if that template changes.
_PLAUSIBLE = {
    "pb_210": (285.0, 14.0),
    "ra_226": (96.0, 5.5),
    "am_241": (12.4, 2.1),
    "cs_137": (41.7, 3.0),
    "k_40": (612.0, 25.0),
}
_FALLBACK = (100.0, 5.0)


@st.cache_data(show_spinner=False)
def _sample_row() -> pd.DataFrame:
    """One synthetic sample: the default template's measured columns, with values."""
    config = BuildConfig.from_template(None, samples=[], geometry=False)
    rows = [
        {
            "Column": col.name,
            "Key": col.key,
            "Activity": _PLAUSIBLE.get(col.key, _FALLBACK)[0],
            "Uncertainty": _PLAUSIBLE.get(col.key, _FALLBACK)[1],
        }
        for col in config.columns
        if col.source is not None  # derived columns are what we are here to test
    ]
    return pd.DataFrame(rows)


st.subheader("Sample values", divider="grey")
st.caption(
    "One synthetic sample, in mBq/g. Edit the numbers to see how they propagate — "
    "nothing here touches your loaded reports or your synthesis."
)
edited = st.data_editor(
    _sample_row(),
    hide_index=True,
    width="stretch",
    disabled=["Column", "Key"],
    column_config={
        "Column": st.column_config.TextColumn("Column", help="The name to use inside [ ]"),
        "Key": st.column_config.TextColumn("Formula key", help="What [Column] resolves to"),
        "Activity": st.column_config.NumberColumn("Activity", format="%.2f"),
        "Uncertainty": st.column_config.NumberColumn("Uncertainty (1σ)", format="%.2f"),
    },
    key="formula_tester_values",
)

namespace = {
    row.Key: Measurement(float(row.Activity), float(row.Uncertainty))
    for row in edited.itertuples()
}

st.subheader("Try a formula", divider="grey")
expr = st.text_input(
    "Formula",
    value="=[PB-210] - [RA-226]",
    help="Reference a column as [Name]. Only + - * /, numbers and parentheses are allowed.",
    key="formula_tester_expr",
)

if not expr.strip():
    st.info("Type a formula above to evaluate it.")
    st.stop()

# Exactly the preprocessing parse_template applies to an `=` cell.
parsed = expand_formula_refs(expr)
st.caption("With the `[Name]` references resolved, this is what gets evaluated:")
st.code(parsed or "(empty)", language="python")

try:
    result = evaluate_formula(parsed, namespace)
except SyntaxError as e:
    st.error(f"Not valid arithmetic: {e.msg}")
except ZeroDivisionError:
    st.error("Division by zero.")
except ValueError as e:
    st.error(str(e))
else:
    value_col, uncertainty_col = st.columns(2)
    value_col.metric("Activity", f"{result.value:,.3f} mBq/g")
    uncertainty_col.metric("Uncertainty (1σ)", f"± {result.uncertainty:,.3f} mBq/g")
    if result.is_nan:
        st.warning("The result is blank — a referenced column has no usable measurement.")
