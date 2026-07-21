"""Roadmap page: load the sample list that drives Chenin, no hand-editing required."""

import io
import tempfile
from importlib import resources
from pathlib import Path

import pandas as pd
import streamlit as st

from chenin.synthesis import BuildConfig
from chenin.ui.components.sidebar import load_build_config

_BLANK_ROADMAP = pd.DataFrame(
    [
        {
            "LSM Code": "CORE-01",
            "Sample Code": "CORE-01-1",
            "Depth Top": 0.0,
            "Depth Bot": 0.5,
            "DBD": 0.0,
            "G2K Report": "report_1.txt",
        },
        {
            "LSM Code": "CORE-01",
            "Sample Code": "CORE-01-2",
            "Depth Top": 0.5,
            "Depth Bot": 1.0,
            "DBD": 0.0,
            "G2K Report": "report_2.txt",
        },
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
# ----------------------- 1. Load a roadmap -------------------------------------------- #
st.subheader("1. Load a roadmap", divider="gray")


roadmap_file = st.file_uploader(
    "Roadmap file (.csv / .xlsx)",
    type=["csv", "xlsx", "xls"],
    help="Columns: LSM Code, Sample Code, Depth Top, Depth Bot, DBD, G2K Report. "
    "Leave 'G2K Report' empty for a planned but unmeasured layer.",
)

report_source = st.segmented_control(
    "Reports location",
    ["Upload files", "Local folder"],
    selection_mode="single",
    default="Upload files",
)

reports_dir = None
report_files = None
if report_source == "Local folder":
    reports_dir = st.text_input(
        "Reports folder",
        value=".",
        help="Folder holding the G2K report files listed in the roadmap, on the "
        "machine running Chenin (relative to where it was launched, or an "
        "absolute path). Only works when Chenin runs on your own machine — not "
        "when the app is deployed to a server.",
    )
else:
    report_files = st.file_uploader(
        "Report files (.txt)",
        type=["txt"],
        accept_multiple_files=True,
        help="Upload the G2K report files listed in the roadmap's 'G2K Report' "
        "column. Works whether Chenin runs locally or is deployed remotely.",
    )

with st.expander("Exemple template"):
    st.dataframe(_BLANK_ROADMAP)


# ----------------------- 2. Load a Synthesis template --------------------------------- #
st.subheader("2. Load a Synthesis template ", divider="gray")

template_source = st.segmented_control(
    "Synthesis template", ["Use default", "Upload custom"], selection_mode="single"
)

synthesis_file = None
if template_source == "Upload custom":
    synthesis_file = st.file_uploader("Custom template (.csv)", type=["csv"])
    if synthesis_file is None:
        st.info("Upload a synthesis template above to continue.", icon=":material/info:")
        st.stop()
else:
    st.caption("Using the packaged lab default (PB-210, RA-226, PB-Exc, AM-241, CS-137, K-40).")
    with st.expander("Default template"):
        st.dataframe(pd.read_csv(io.StringIO(_default_template_text())))

# ----------------------- 3. Load into app --------------------------------------------- #
st.subheader("3. Load into app", divider="gray")

if roadmap_file is None:
    st.info("Upload a roadmap above to continue.", icon=":material/info:")
    st.stop()

try:
    config = BuildConfig.from_roadmap(roadmap_file, synthesis_file)
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
    if report_files:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            for f in report_files:
                (tmp_dir / f.name).write_bytes(f.getvalue())
            loaded = load_build_config(config, tmp_dir)
    else:
        loaded = load_build_config(config, Path(reports_dir or "."))

    if loaded:
        st.session_state["_build_file_key"] = ("roadmap", id(config))
        st.success("Loaded — see the Reports and Synthesis pages.")
    else:
        st.warning("No reports were loaded — check the reports above.")
