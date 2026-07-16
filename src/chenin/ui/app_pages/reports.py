import io
import zipfile

import pandas as pd
import streamlit as st

from chenin.g2k_parser import SECTION_DESCRIPTIONS
from chenin.ui import state
from chenin.ui.components.dataframe_view_mode import df_view_mode_widget
from chenin.ui.components.export import export_dataframe

pd.set_option("display.float_format", lambda x: f"{x:f}")

st.title("Reports")
st.caption("Every extracted section of every loaded report.")

reports = state.get_reports()

if not reports:
    st.info("Load a roadmap on the Roadmap page to see its reports here.")
    st.stop()


def _export_all_zip(reports: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, report in reports.items():
            for key in report:
                csv = report[key].to_csv(sep=";", index=False, float_format="%.6f")
                zf.writestr(f"{name}/{key}.csv", csv)
    return buf.getvalue()


st.download_button(
    label="Export all (ZIP)",
    data=_export_all_zip(reports),
    file_name="reports.zip",
    mime="application/zip",
    icon=":material/download:",
)

tabs = st.tabs(list(reports.keys()))

for tab, (name, report) in zip(tabs, reports.items(), strict=True):
    with tab:
        st.subheader("Sections", divider="gray")

        for key in report:
            df = report[key]

            with st.container(border=True):
                st.markdown(f"##### {SECTION_DESCRIPTIONS[key]}")

                df_view_mode_widget(df, name, key)

                export_dataframe(df, filename=f"{name}-{key}")
