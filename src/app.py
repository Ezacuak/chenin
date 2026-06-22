import streamlit as st

st.title("Chenin")
st.markdown("A tool to extract data from `Génie200` report.")
st.divider()

pages = {
    "Tools": [
        st.Page("pages/report.py", title="Rapport Génie2000"),
        st.Page("pages/summary.py", title="Synthèse des rapport"),
    ]
}

pg = st.navigation(pages)
pg.run()
