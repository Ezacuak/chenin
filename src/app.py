import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from extraction import Report


@st.cache_data
def load_report(file_path: str) -> Report:
    return Report.from_file(file_path)


def plot_s2_energy_vs_surface(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df["Energie (keV)"], df["Surface"], alpha=0.6, s=50)
    ax.set_xlabel("Energy (keV)", fontsize=12)
    ax.set_ylabel("Surface", fontsize=12)
    ax.set_title("Peak Energy vs. Surface", fontsize=14, fontweight="bold")
    ax.grid(alpha=0.3)
    st.pyplot(fig)


def plot_s2_fwhm_histogram(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(df["FWHM (keV)"], bins=30, alpha=0.7, color="steelblue", edgecolor="black")
    ax.set_xlabel("FWHM (keV)", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.set_title("FWHM Distribution", fontsize=14, fontweight="bold")
    ax.grid(alpha=0.3, axis="y")
    st.pyplot(fig)


def show_s2_section(report: Report):
    st.header("📊 S2 - Peak Analysis (RAPPORT ANALYSE DES PICS)")

    df = report.extract_s2()

    if df.empty:
        st.warning("No S2 data found in report")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Peaks", len(df))
    with col2:
        st.metric("Energy Range (keV)", f"{df['Energie (keV)'].min():.1f} - {df['Energie (keV)'].max():.1f}")
    with col3:
        st.metric("Avg FWHM (keV)", f"{df['FWHM (keV)'].mean():.2f}")
    with col4:
        st.metric("Total Surface", f"{df['Surface'].sum():.0f}")

    st.subheader("Peak Data Table")
    st.dataframe(df, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Energy vs. Surface")
        plot_s2_energy_vs_surface(df)

    with col2:
        st.subheader("FWHM Distribution")
        plot_s2_fwhm_histogram(df)

    energy_min, energy_max = st.slider(
        "Filter by Energy Range (keV)",
        min_value=float(df["Energie (keV)"].min()),
        max_value=float(df["Energie (keV)"].max()),
        value=(float(df["Energie (keV)"].min()), float(df["Energie (keV)"].max())),
        step=1.0,
    )

    filtered_df = df[
        (df["Energie (keV)"] >= energy_min) & (df["Energie (keV)"] <= energy_max)
    ]
    st.subheader(f"Filtered Data ({len(filtered_df)} peaks)")
    st.dataframe(filtered_df, use_container_width=True)


def show_s6_section(report: Report):
    st.header("🔬 S6 - Detection Limits (ISO 11929)")

    df = report.extract_s6()

    if df.empty:
        st.warning("No S6 data found in report")
        return

    marker_counts = df["Marker"].value_counts() if "Marker" in df.columns else {}
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Nucleides", len(df))
    with col2:
        identified = (df["Marker"] == "+").sum() if "Marker" in df.columns else 0
        st.metric("Identified (+)", identified)
    with col3:
        uncertain = (df["Marker"] == "?").sum() if "Marker" in df.columns else 0
        st.metric("Uncertain (?)", uncertain)

    st.subheader("Nucleide Detection Limits")
    st.dataframe(df, use_container_width=True)

    if "Marker" in df.columns:
        st.subheader("Filter by Marker")
        marker_filter = st.multiselect(
            "Select markers",
            options=df["Marker"].unique(),
            default=df["Marker"].unique().tolist(),
        )
        filtered_df = df[df["Marker"].isin(marker_filter)]
        st.dataframe(filtered_df, use_container_width=True)


def main():
    st.set_page_config(page_title="Génie200 Report Extractor", layout="wide")
    st.title("📈 Génie200 Report Data Extractor")

    st.sidebar.title("📁 Upload Report")
    uploaded_file = st.sidebar.file_uploader("Choose a Génie200 report (.txt)", type=["txt"])

    if uploaded_file is None:
        st.info("👈 Upload a Génie200 report to get started")
        return

    with st.spinner("Processing report..."):
        temp_path = Path("/tmp") / uploaded_file.name
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        report = load_report(str(temp_path))

    st.sidebar.success(f"✓ Loaded: {uploaded_file.name}")

    tab1, tab2 = st.tabs(["📊 S2 - Peak Analysis", "🔬 S6 - Detection Limits"])

    with tab1:
        show_s2_section(report)

    with tab2:
        show_s6_section(report)


if __name__ == "__main__":
    main()
