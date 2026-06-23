import streamlit as st

st.title("Chenin")
st.markdown("A tool to extract data from `Génie200` report.")
st.divider()

pages = {
    "Outils": [
        st.Page("pages/report.py", title="Extracteur de rapport"),
        st.Page("pages/synthesis.py", title="Constructeur de synthese"),
    ]
}

pg = st.navigation(pages)
pg.run()
