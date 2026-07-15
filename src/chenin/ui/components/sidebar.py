from pathlib import Path

import streamlit as st

from chenin.synthesis import BuildConfig, load_reports
from chenin.ui import state


def load_build_config(config: BuildConfig, base_dir: Path | None = None) -> bool:
    """Load a build config's reports from disk and store both in session state.

    ``base_dir`` defaults to the current working directory (where Chenin was
    launched). Returns True on success. On failure, shows an error and leaves the
    previous session state untouched.
    """
    try:
        reports = load_reports(config, base_dir or Path.cwd())
    except (FileNotFoundError, OSError) as e:
        st.error(f"Could not load reports: {e}")
        return False
    state.store_build(config, reports)
    return True


def render_build_sidebar() -> None:
    """Sidebar section for loading the roadmap that drives the whole app."""
    with st.sidebar:
        st.subheader("Roadmap", anchor=False)
        roadmap_file = st.file_uploader(
            "Import a roadmap (.csv / .xlsx)",
            type=["csv", "xlsx", "xls"],
            accept_multiple_files=False,
            help=(
                "The roadmap lists the core's samples (report file + layer depths). "
                "The standard synthesis template is applied automatically."
            ),
        )

        if roadmap_file is not None:
            # Only (re)load when a new file is dropped.
            file_key = (roadmap_file.name, roadmap_file.size)
            if st.session_state.get("_build_file_key") != file_key:
                try:
                    config = BuildConfig.from_roadmap(roadmap_file)
                except (ValueError, KeyError) as e:
                    st.error(f"Invalid roadmap: {e}")
                else:
                    if load_build_config(config):
                        st.session_state["_build_file_key"] = file_key

        config = state.get_build_config()
        if config is not None:
            st.success(f"{len(config.samples)} sample(s) loaded — “{config.title}”")
        else:
            st.caption("No roadmap loaded yet.")
