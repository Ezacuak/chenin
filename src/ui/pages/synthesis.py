import state
import streamlit as st

from synthesis import SynthesisBuilder

st.title("Synthèse")
st.markdown("Construire une synthèse à partir des rapports chargés.")

with st.sidebar:
    st.header("Modèle de synthèse")
    synthesis_file = st.file_uploader(
        "Sélectionner le fichier de synthèse (.toml)",
        type=["toml"],
        accept_multiple_files=False,
    )

reports, errors = state.get_reports()

for name, message in errors.items():
    st.error(f"Échec de l'analyse de {name} : {message}")

if not reports:
    st.info(
        "Chargez un ou plusieurs fichiers de rapport G2K avec l'outil d'extraction de rapport."
    )
    st.stop()

if not synthesis_file:
    st.info(
        "Chargez un fichier de configuration .toml (ou cochez « modèle par défaut »)."
    )
    st.stop()

# ----------------------------- Contruction de la synthese -----------------------------#

with st.container(border=True):
    builder = SynthesisBuilder.from_toml()









# ------------------------------ Affichage de la synthese ------------------------------#
df = state.get_synthesis()
if df is None:
    st.info("Cliquez sur « Générer » pour construire la synthèse.")
    st.stop()

st.dataframe(df)

st.download_button(
    "Télécharger en CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="synthese.csv",
    mime="text/csv",
)
