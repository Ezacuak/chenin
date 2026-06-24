import streamlit as st

st.title("Chenin")
st.badge("PTAL")
st.markdown("Un outil d'analyse de donnée pour les rapports de `Génie200`.")
st.info("En cours de developpement !")
st.divider()

pages = {
    "Outils": [
        st.Page("pages/report.py", title="Extracteur de rapport"),
        st.Page("pages/synthesis.py", title="Constructeur de synthese"),
        # st.Page("pages/carotte.py", title="Visualisation carotte"),
    ]
}

pg = st.navigation(pages)
pg.run()
