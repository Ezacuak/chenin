import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "ui"))

import streamlit as st

from synthesis import BuildConfig, load_reports
from ui import state

st.set_page_config(layout="wide")

st.title("Chenin")
st.badge("PTAL")
st.markdown("Un outil d'analyse de donnée pour les rapports de `Génie200`.")
st.info("En cours de developpement !")
st.divider()

# ------------------------- Import global du fichier build ------------------------- #
# Point d'entrée unique : le fichier build référence les échantillons (+ profondeurs)
# ET le format de synthèse. Les pages consomment l'état partagé.
with st.sidebar:
    st.header("Fichier build")
    build_file = st.file_uploader(
        "Importer le fichier build (.toml)",
        type=["toml"],
        accept_multiple_files=False,
    )

    if build_file is not None:
        # Ne (re)charge que lorsqu'un nouveau fichier est déposé.
        file_key = (build_file.name, build_file.size)
        if st.session_state.get("_build_file_key") != file_key:
            try:
                config = BuildConfig.from_toml(build_file)
                reports = load_reports(config, Path.cwd())
            except (ValueError, FileNotFoundError, KeyError) as e:
                st.error(f"Fichier build invalide : {e}")
            else:
                state.store_build(config, reports)
                st.session_state["_build_file_key"] = file_key

        config = state.get_build_config()
        if config is not None:
            st.success(f"{len(config.samples)} échantillons chargés")

    st.divider()

pages = {
    "Outils": [
        st.Page("ui/pages/report_page.py", title="Extracteur de rapport"),
        st.Page("ui/pages/synthesis_page.py", title="Constructeur de synthese"),
    ]
}

pg = st.navigation(pages)
pg.run()
