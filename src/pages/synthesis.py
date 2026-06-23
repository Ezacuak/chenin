import streamlit as st

import state

st.title("Synthèse")
st.markdown("Construire une synthèse à partir des rapports chargés.")

with st.sidebar:
    st.header("Ouvire le template de synthèse")
    synthesis_file = st.file_uploader(
        "Selectionner le fichier de synthèse (.toml)",
        type=["toml"],
        accept_multiple_files=False,
    )

    st.button("Génerer", type="primary")

reports, errors = state.get_reports()

for name, message in errors.items():
    st.error(f"Échec de l'analyse de {name} : {message}")

if not reports:
    st.info(
        "Chargez un ou plusieurs fichiers de rapport G2K avec l'outil d'extraction de rapport"
    )
    st.stop()

if not synthesis_file:
    st.info(" Charger un fichier de generation de rapport")
    st.stop()

for k in reports.keys():
    st.markdown(f"""{k}""")
