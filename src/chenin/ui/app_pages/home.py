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

reports = state.get_reports()

step1, step2, step3 = st.columns(3, border=True)


with step1:
    st.markdown("##### :material/tune: 1. Load Data")
    st.markdown("Load data from 'Génie2000' reports.")
    if not reports:
        st.caption(":material/radio_button_unchecked: Not loaded yet")
        if st.button("Load reports", key="home_to_editor"):
            st.switch_page(str(Path(__file__).parent / "data_loader.py"))
    else:
        st.caption(f":material/check_circle: {len(reports)} loaded")

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
        st.caption(":material/radio_button_unchecked: Waiting for reports file")

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
