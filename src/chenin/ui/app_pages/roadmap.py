"""Roadmap page: load the sample list that drives Chenin, no hand-editing required."""

from importlib import resources
from pathlib import Path

import pandas as pd
import streamlit as st

from chenin.synthesis import BuildConfig
from chenin.ui.components.sidebar import load_build_config

_BLANK_ROADMAP = pd.DataFrame(
    [
        {"LSM Code": "CORE-01", "Sample Code": "CORE-01-1", "Depth Top": 0.0,
         "Depth Bot": 0.5, "DBD": 0.0, "G2K Report": "report_1.txt"},
        {"LSM Code": "CORE-01", "Sample Code": "CORE-01-2", "Depth Top": 0.5,
         "Depth Bot": 1.0, "DBD": 0.0, "G2K Report": "report_2.txt"},
    ]
)


def _default_template_text() -> str:
    ref = resources.files("chenin.synthesis") / "default_template.csv"
    return ref.read_text(encoding="utf-8")


st.title("Roadmap file")
st.caption(
    "A roadmap lists the core's samples — one row per layer, with its report file, "
    "depths and density. It is the single input Chenin needs: the standard synthesis "
    "template (PB-210, RA-226, PB-Exc, AM-241, CS-137, K-40) is applied automatically."
)

st.subheader("1. Load a roadmap", divider="gray")
st.download_button(
    "Download a blank roadmap template",
    data=_BLANK_ROADMAP.to_csv(index=False).encode("utf-8"),
    file_name="roadmap-template.csv",
    mime="text/csv",
    icon=":material/download:",
)
roadmap_file = st.file_uploader(
    "Roadmap file (.csv / .xlsx)",
    type=["csv", "xlsx", "xls"],
    help="Columns: LSM Code, Sample Code, Depth Top, Depth Bot, DBD, G2K Report. "
    "Leave 'G2K Report' empty for a planned but unmeasured layer.",
)

reports_dir = st.text_input(
    "Reports folder",
    value=".",
    help="Folder holding the G2K report files listed in the roadmap "
    "(relative to where Chenin was launched, or an absolute path).",
)

with st.expander("Advanced: custom synthesis template", icon=":material/tune:"):
    st.caption(
        "The wide template has one column per output; its single method row is either "
        "gamma peaks (`NUCLIDE@energy`, `;`-separated for a weighted mean) or an `=` "
        "formula over other columns, e.g. `=[PB-210] - [RA-226]`. Upload one to override "
        "the packaged default below."
    )
    st.code(_default_template_text(), language="text")
    template_file = st.file_uploader("Custom template (.csv)", type=["csv"])

st.subheader("2. Load into app", divider="gray")

if roadmap_file is None:
    st.info("Upload a roadmap above to continue.", icon=":material/info:")
    st.stop()

try:
    config = BuildConfig.from_roadmap(roadmap_file, template_file)
except (ValueError, KeyError) as e:
    st.error(f"Roadmap is not valid yet: {e}", icon=":material/error:")
    st.stop()

measured = sum(1 for s in config.samples if s.name)
st.success(
    f"Valid — “{config.title}”: {len(config.samples)} sample(s), {measured} with a report, "
    f"{len(config.columns)} synthesis column(s).",
    icon=":material/check_circle:",
)
st.dataframe(
    pd.DataFrame(
        [
            {
                "Sample": s.sample_code,
                "Report": s.name or "—",
                "Depth top (cm)": s.depth_top,
                "Depth bottom (cm)": s.depth_bot,
                "DBD": s.dbd,
            }
            for s in config.samples
        ]
    ),
    width="stretch",
    hide_index=True,
)

if st.button("Load into app", icon=":material/rocket_launch:", type="primary"):
    if load_build_config(config, Path(reports_dir or ".")):
        st.session_state["_build_file_key"] = ("roadmap", id(config))
        st.success("Loaded — see the Reports and Synthesis pages.")
    else:
        st.warning("No reports were loaded — check the reports folder path above.")
