import pandas as pd
import state
import streamlit as st
from components.export import export_dataframe

from synthesis import SynthesisBuilder, SynthesisConfig

st.title("Synthèse")
st.markdown("Construire une synthèse à partir des rapports chargés.")

with st.sidebar:
    st.header("Modèle de synthèse")
    toml_synthesis_file = st.file_uploader(
        "Sélectionner le fichier de synthèse (.toml)",
        type=["toml"],
        accept_multiple_files=False,
    )

reports = state.get_reports()

if not reports:
    st.info(
        "Chargez un ou plusieurs fichiers de rapport G2K avec l'outil d'extraction de rapport."
    )
    st.stop()

if not toml_synthesis_file:
    st.info(
        "Chargez un fichier de configuration .toml (ou cochez « modèle par défaut »)."
    )
    st.stop()

# ----------------------------- Affichage pre synthese ----------------------------#

try:
    config = SynthesisConfig.from_toml(toml_synthesis_file)
except ValueError as e:
    st.error(f"Configuration invalide : {e}")
    st.stop()

with st.expander(f"Configuration : {config.title}", expanded=True):
    md_metadata = f"""
**Metadata:** :green-badge[Année: {config.metadata.base_year}] :green-badge[Taux de sedimentation: {config.metadata.taux_sedimentation}] :green-badge[Epaisseur: {config.metadata.epaisseur}]
"""
    st.markdown(md_metadata)

    st.markdown("**Nuclides:**")
    for key, nuclide in config.nuclides.items():
        peaks = ", ".join(f"{p.nuclide} @ {p.energy} keV" for p in nuclide.peaks)
        st.text(f"{key}: {peaks}")

    st.markdown("**Colonnes:**")

    # preview_df = pd.DataFrame(columns=cols)
    for column in config.columns:
        source = (
            f"source={column.source}"
            if column.source is not None
            else f"formule={column.formula}"
        )
        st.text(f"{column.key} ({column.name}): {source}")


st.divider()

# ----------------------------- Construction de la synthese ----------------------------#
builder = SynthesisBuilder(config)

ordered_reports = [reports[k] for k in sorted(reports)]

if st.button("Générer la synthèse", type="primary"):
    try:
        df = builder.build(ordered_reports)
        state.store_synthesis(df)
    except Exception as e:
        st.error(f"Erreur lors de la génération : {e}")
        st.stop()
# ------------------------------ Affichage de la synthese ------------------------------#
with st.container(border=True):
    df = state.get_synthesis()
    if df is None:
        st.info("Cliquez sur « Générer » pour construire la synthèse.")
        st.stop()

    st.dataframe(df)

    export_dataframe(df, filename="synthese")
