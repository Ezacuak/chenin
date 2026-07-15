from pathlib import Path

import streamlit as st

from chenin.ui import state

st.title("Chenin")
st.caption("Génie 2000 report extraction and sediment-core synthesis — EDYTEM-PTAL")

st.markdown(
    "Chenin turns **Génie 2000 (G2K)** gamma-spectrometry reports into structured "
    "data and builds an **activity-vs-depth synthesis** for a sediment core, ready "
    "for age-depth modelling."
)

config = state.get_build_config()

step1, step2, step3 = st.columns(3, border=True)

with step1:
    st.markdown("##### :material/tune: 1. Build file")
    st.markdown(
        "A build file lists the core's samples (report + layer depths) and the "
        "synthesis format (nuclides, columns)."
    )
    if config is None:
        st.caption(":material/radio_button_unchecked: Not loaded yet")
        if st.button("Create one", key="home_to_editor"):
            st.switch_page(str(Path(__file__).parent / "build_editor.py"))
    else:
        st.caption(f":material/check_circle: “{config.title}” loaded")

with step2:
    st.markdown("##### :material/description: 2. Reports")
    st.markdown(
        "Inspect every extracted section of each report — peaks, nuclide activities, "
        "detection limits — and export them individually."
    )
    reports = state.get_reports()
    if reports:
        st.caption(f":material/check_circle: {len(reports)} report(s) loaded")
    else:
        st.caption(":material/radio_button_unchecked: Waiting on a build file")

with step3:
    st.markdown("##### :material/insights: 3. Synthesis")
    st.markdown(
        "One row per sample with activities, uncertainties and depth — visualised as "
        "a core profile, then exported to CSV, Parquet or SERAC."
    )
    synthesis = state.get_synthesis()
    if synthesis is not None:
        st.caption(f":material/check_circle: {len(synthesis)} row(s) built")
    else:
        st.caption(":material/radio_button_unchecked: Not built yet")

st.divider()

with st.expander("What is a Génie 2000 report?", icon=":material/help:"):
    st.markdown(
        "A plain-text export from the Canberra/Mirion **Génie 2000** gamma spectrometry "
        "software, split into six sections: spectrum metadata, peak analysis, nuclide "
        "identification, interference-corrected identification, and two detection-limit "
        "reports. Chenin parses all six into tables."
    )

with st.expander("Where does depth come from?", icon=":material/help:"):
    st.markdown(
        "G2K reports don't carry sample depth — it's field data. The build file's "
        "`[[samples]]` list supplies `depth_top`/`depth_bot` (cm) for each report, in "
        "core order."
    )
