from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Chenin",
    page_icon=":material/science:",
    layout="wide",
)

_PAGES_DIR = Path(__file__).parent / "app_pages"

pages = {
    "": [
        st.Page(_PAGES_DIR / "home.py", title="Home", icon=":material/home:"),
    ],
    "Workflow": [
        st.Page(_PAGES_DIR / "roadmap.py", title="Roadmap file", icon=":material/tune:"),
        st.Page(_PAGES_DIR / "reports.py", title="Reports", icon=":material/description:"),
        st.Page(_PAGES_DIR / "synthesis.py", title="Synthesis", icon=":material/insights:"),
    ],
}

pg = st.navigation(pages, position="top")
pg.run()
