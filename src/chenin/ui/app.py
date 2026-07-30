from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Chenin",
    page_icon=":material/science:",
    layout="wide",
)

_PAGES_DIR = Path(__file__).parent / "app_pages"
_DOCS_DIR = _PAGES_DIR / "docs"

pages = {
    "": [
        st.Page(_PAGES_DIR / "home.py", title="Home", icon=":material/home:"),
    ],
    "Workflow": [
        st.Page(_PAGES_DIR / "data_loader.py", title="Load Data", icon=":material/tune:"),
        st.Page(_PAGES_DIR / "reports.py", title="Reports", icon=":material/description:"),
        st.Page(_PAGES_DIR / "synthesis.py", title="Synthesis", icon=":material/insights:"),
    ],
    # Each of these is a two-line stub rendering docs/guide/<name>.md — see
    # ui/components/doc_page.py. Order here is the reading order.
    "Documentation": [
        st.Page(_DOCS_DIR / "overview.py", title="Overview", icon=":material/menu_book:"),
        st.Page(_DOCS_DIR / "install.py", title="Install & Update", icon=":material/download:"),
        st.Page(
            _DOCS_DIR / "loading-reports.py",
            title="Loading Reports",
            icon=":material/upload_file:",
        ),
        st.Page(_DOCS_DIR / "core-layers.py", title="Core Layers", icon=":material/layers:"),
        st.Page(
            _DOCS_DIR / "building-columns.py",
            title="Building Columns",
            icon=":material/view_column:",
        ),
        st.Page(
            _DOCS_DIR / "synthesis-template.py",
            title="Templates",
            icon=":material/table_chart:",
        ),
        st.Page(_DOCS_DIR / "formulas.py", title="Formulas", icon=":material/functions:"),
        st.Page(
            _DOCS_DIR / "formula-tester.py",
            title="Formula Tester",
            icon=":material/calculate:",
        ),
        st.Page(_DOCS_DIR / "exporting.py", title="Exporting", icon=":material/save:"),
        st.Page(_DOCS_DIR / "command-line.py", title="Command Line", icon=":material/terminal:"),
        st.Page(
            _DOCS_DIR / "troubleshooting.py",
            title="Troubleshooting",
            icon=":material/help:",
        ),
    ],
}

# Past twelve pages Streamlit collapses the sidebar behind a "View more" button; this
# app has fifteen and uses st.sidebar on the Synthesis page, so pin it open.
pg = st.navigation(pages, expanded=True)
pg.run()
