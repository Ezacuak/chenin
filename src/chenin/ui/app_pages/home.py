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
    st.markdown("##### :material/tune: 1. Roadmap file")
    st.markdown("A roadmap file lists the core's samples (metadata + report file)")
    if config is None:
        st.caption(":material/radio_button_unchecked: Not loaded yet")
        if st.button("Create one", key="home_to_editor"):
            st.switch_page(str(Path(__file__).parent / "roadmap.py"))
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
        st.caption(":material/radio_button_unchecked: Waiting on a roadmap file")

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
