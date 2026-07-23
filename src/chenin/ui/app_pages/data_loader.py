"""Load Data page: upload G2K report files and parse them into the session."""

import tempfile
from pathlib import Path

import streamlit as st

from chenin.g2k_parser import Report
from chenin.ui import state

st.title("Load Data")

st.caption("Upload the Génie 2000 (.txt) report files for this core.")

uploaded_files = st.file_uploader(
    "G2K reports (.txt)", type="txt", accept_multiple_files=True
)

if uploaded_files:
    file_key = tuple((f.name, f.size) for f in uploaded_files)
    if st.session_state.get("_data_loader_file_key") != file_key:
        reports: dict[str, Report] = {}
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            for f in uploaded_files:
                tmp_path = tmp_dir / f.name
                tmp_path.write_bytes(f.getvalue())
                try:
                    report = Report(tmp_path, name=tmp_path.stem)
                except (ValueError, KeyError) as e:
                    st.error(f"Could not parse {f.name}: {e}")
                    continue
                reports[report.name] = report

        state.store_reports(reports)
        st.session_state["_data_loader_file_key"] = file_key

reports = state.get_reports()
if reports:
    st.success(f"{len(reports)} report(s) loaded.")
    st.dataframe({"Report": list(reports.keys())}, hide_index=True, width="stretch")
