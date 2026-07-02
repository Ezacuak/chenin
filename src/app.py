import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "ui"))

import streamlit as st

st.set_page_config(layout="wide")

st.title("Chenin")
st.badge("PTAL")
st.markdown("Un outil d'analyse de donnée pour les rapports de `Génie200`.")
st.info("En cours de developpement !")
st.divider()

pages = {
    "Outils": [
        st.Page("ui/pages/report.py", title="Extracteur de rapport"),
        st.Page("ui/pages/synthesis_page.py", title="Constructeur de synthese"),
    ]
}

pg = st.navigation(pages)
pg.run()
