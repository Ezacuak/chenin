from pathlib import Path

import streamlit as st

from chenin.ui.components.sidebar import render_build_sidebar

st.set_page_config(
    page_title="Chenin",
    page_icon=":material/science:",
    layout="wide",
)

render_build_sidebar()

_PAGES_DIR = Path(__file__).parent / "app_pages"

pages = {
    "": [
        st.Page(_PAGES_DIR / "home.py", title="Home", icon=":material/home:"),
    ],
    "Workflow": [
        st.Page(_PAGES_DIR / "build_editor.py", title="Build file", icon=":material/tune:"),
        st.Page(_PAGES_DIR / "reports.py", title="Reports", icon=":material/description:"),
        st.Page(_PAGES_DIR / "synthesis.py", title="Synthesis", icon=":material/insights:"),
    ],
    "Help": [
        st.Page(
            _PAGES_DIR / "documentation.py", title="Documentation", icon=":material/menu_book:"
        ),
    ],
}

pg = st.navigation(pages, position="top")
pg.run()
