"""Sidebar build-file loader, shared by every page via the app-level entry point."""

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
    """Sidebar section for loading the build file that drives the whole app."""
    with st.sidebar:
        st.subheader("Build file", anchor=False)
        build_file = st.file_uploader(
            "Import a build file (.toml)",
            type=["toml"],
            accept_multiple_files=False,
            help=(
                "The build file lists the samples (report + layer depths) and the "
                "synthesis format. Create one on the Build file page, or write it by hand — "
                "see the documentation for the schema."
            ),
        )

        if build_file is not None:
            # Only (re)load when a new file is dropped.
            file_key = (build_file.name, build_file.size)
            if st.session_state.get("_build_file_key") != file_key:
                try:
                    config = BuildConfig.from_toml(build_file)
                except (ValueError, KeyError) as e:
                    st.error(f"Invalid build file: {e}")
                else:
                    if load_build_config(config):
                        st.session_state["_build_file_key"] = file_key

        config = state.get_build_config()
        if config is not None:
            st.success(f"{len(config.samples)} sample(s) loaded — “{config.title}”")
        else:
            st.caption("No build file loaded yet.")
