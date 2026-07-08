"""Build file editor: create or edit a build TOML from the UI, no hand-editing required."""

import math

import pandas as pd
import streamlit as st

from chenin.synthesis import BuildConfig
from chenin.ui import state
from chenin.ui.components.sidebar import load_build_config

_SAMPLES_COLS = ["Report file", "Depth top (cm)", "Depth bottom (cm)"]
_NUCLIDES_COLS = ["Key", "Peak nuclide", "Energy (keV)"]
_COLUMNS_COLS = ["Key", "Display name", "Source (nuclide key)", "Formula"]


def _blank_seed() -> dict:
    return {
        "title": "New synthesis",
        "description": "",
        "base_path": "./data",
        "samples": pd.DataFrame(
            [{"Report file": "sample_1.txt", "Depth top (cm)": 0.0, "Depth bottom (cm)": 1.0}]
        ),
        "base_year": None,
        "taux_sedimentation": None,
        "coring_yr": None,
        "nuclides": pd.DataFrame(
            [{"Key": "pb210", "Peak nuclide": "PB-210", "Energy (keV)": 46.54}]
        ),
        "columns": pd.DataFrame(
            [
                {
                    "Key": "pb210",
                    "Display name": "PB-210",
                    "Source (nuclide key)": "pb210",
                    "Formula": "",
                }
            ]
        ),
    }


def _df_or_empty(rows: list[dict], columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=columns)


def _clean_float(value) -> float | None:
    """Coerce a data-editor cell to a float, treating missing/NaN/blank as None."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def _config_to_seed(config: BuildConfig) -> dict:
    samples = _df_or_empty(
        [
            {
                "Report file": s.name,
                "Depth top (cm)": s.depth_top,
                "Depth bottom (cm)": s.depth_bot,
            }
            for s in config.samples
        ],
        _SAMPLES_COLS,
    )

    nuclides = _df_or_empty(
        [
            {"Key": key, "Peak nuclide": p.nuclide, "Energy (keV)": p.energy}
            for key, spec in config.nuclides.items()
            for p in spec.peaks
        ],
        _NUCLIDES_COLS,
    )

    columns = _df_or_empty(
        [
            {
                "Key": c.key,
                "Display name": c.name,
                "Source (nuclide key)": c.source or "",
                "Formula": c.formula or "",
            }
            for c in config.columns
        ],
        _COLUMNS_COLS,
    )

    return {
        "title": config.title,
        "description": config.description or "",
        "base_path": config.base_path or "",
        "samples": samples,
        "base_year": config.metadata.base_year,
        "taux_sedimentation": config.metadata.taux_sedimentation,
        "coring_yr": config.metadata.coring_yr,
        "nuclides": nuclides,
        "columns": columns,
    }


def _build_raw(
    title: str,
    description: str,
    base_path: str,
    samples_df: pd.DataFrame,
    base_year: float | None,
    taux_sedimentation: float | None,
    coring_yr: float | None,
    nuclides_df: pd.DataFrame,
    columns_df: pd.DataFrame,
) -> dict:
    samples = []
    for row in samples_df.to_dict("records"):
        name = str(row.get("Report file") or "").strip()
        top = _clean_float(row.get("Depth top (cm)"))
        bot = _clean_float(row.get("Depth bottom (cm)"))
        if not name or top is None or bot is None:
            continue
        samples.append({"name": name, "depth_top": top, "depth_bot": bot})

    nuclides: dict[str, dict] = {}
    for row in nuclides_df.to_dict("records"):
        key = str(row.get("Key") or "").strip()
        peak_nuclide = str(row.get("Peak nuclide") or "").strip()
        energy = _clean_float(row.get("Energy (keV)"))
        if not key or not peak_nuclide or energy is None:
            continue
        nuclides.setdefault(key, {"peaks": []})["peaks"].append(
            {"nuclide": peak_nuclide, "energy": energy}
        )

    columns: dict[str, dict] = {}
    for row in columns_df.to_dict("records"):
        key = str(row.get("Key") or "").strip()
        if not key:
            continue
        spec: dict = {"name": str(row.get("Display name") or "").strip()}
        source = str(row.get("Source (nuclide key)") or "").strip()
        formula = str(row.get("Formula") or "").strip()
        if source:
            spec["source"] = source
        if formula:
            spec["formula"] = formula
        columns[key] = spec

    metadata = {}
    if base_year is not None:
        metadata["base_year"] = base_year
    if taux_sedimentation:
        metadata["taux_sedimentation"] = taux_sedimentation
    if coring_yr is not None:
        metadata["coring_yr"] = coring_yr

    return {
        "title": title.strip() or "Synthesis",
        "description": description.strip() or None,
        "base_path": base_path.strip() or None,
        "samples": samples,
        "metadata": metadata,
        "nuclides": nuclides,
        "columns": columns,
    }


st.title("Build file")
st.caption(
    "A build file is the single input that drives Chenin: it lists the core's samples "
    "(report + layer depths) and the synthesis format (nuclides, columns). Edit it here "
    "instead of writing TOML by hand."
)

if "editor_version" not in st.session_state:
    st.session_state["editor_version"] = 0
    loaded = state.get_build_config()
    st.session_state["editor_seed"] = _config_to_seed(loaded) if loaded else _blank_seed()

with st.container(horizontal=True):
    if st.button("Start from a blank build file", icon=":material/note_add:"):
        st.session_state["editor_seed"] = _blank_seed()
        st.session_state["editor_version"] += 1
        st.rerun()

    loaded_config = state.get_build_config()
    if loaded_config is not None and st.button(
        "Reload from the active build file", icon=":material/refresh:"
    ):
        st.session_state["editor_seed"] = _config_to_seed(loaded_config)
        st.session_state["editor_version"] += 1
        st.rerun()

seed = st.session_state["editor_seed"]
v = st.session_state["editor_version"]

st.subheader("General", divider="gray")
gen_col1, gen_col2 = st.columns(2)
with gen_col1:
    title = st.text_input("Title", value=seed["title"], key=f"title_{v}")
    base_path = st.text_input(
        "Reports folder (base path)",
        value=seed["base_path"],
        key=f"base_path_{v}",
        help="Path to the folder containing the report files, relative to the current "
        "working directory when Chenin is launched.",
    )
with gen_col2:
    description = st.text_area(
        "Description", value=seed["description"], key=f"description_{v}", height=100
    )

st.subheader("Samples", divider="gray")
st.caption("One row per report, in core order. Depths are in centimetres.")
samples_df = st.data_editor(
    seed["samples"],
    key=f"samples_{v}",
    num_rows="dynamic",
    column_config={
        "Depth top (cm)": st.column_config.NumberColumn(format="%.2f"),
        "Depth bottom (cm)": st.column_config.NumberColumn(format="%.2f"),
    },
    width="stretch",
)

st.subheader("Age model", divider="gray")
st.caption("Optional. Leave blank to omit the Age column from the synthesis.")
age_col1, age_col2, age_col3 = st.columns(3)
with age_col1:
    base_year = st.number_input(
        "Base year", value=seed["base_year"], key=f"base_year_{v}", step=1.0, format="%.0f"
    )
with age_col2:
    taux_sedimentation = st.number_input(
        "Sedimentation rate (cm/yr)",
        value=seed["taux_sedimentation"],
        key=f"taux_sed_{v}",
        format="%.4f",
    )
with age_col3:
    coring_yr = st.number_input(
        "Coring year", value=seed["coring_yr"], key=f"coring_yr_{v}", step=1.0, format="%.0f"
    )

st.subheader("Nuclides", divider="gray")
st.caption(
    "A nuclide is one or more gamma peaks read from section 3 of the report. Give several "
    "peaks the same key to combine them as an inverse-variance weighted mean "
    "(e.g. RA-226 from its PB-214/BI-214 daughters)."
)
nuclides_df = st.data_editor(
    seed["nuclides"],
    key=f"nuclides_{v}",
    num_rows="dynamic",
    column_config={"Energy (keV)": st.column_config.NumberColumn(format="%.2f")},
    width="stretch",
)

st.subheader("Columns", divider="gray")
st.caption(
    "What ends up in the synthesis, in order. Fill exactly one of Source (a nuclide key "
    "above) or Formula (arithmetic over nuclide keys, e.g. `pb210 - ra226`)."
)
columns_df = st.data_editor(
    seed["columns"],
    key=f"columns_{v}",
    num_rows="dynamic",
    width="stretch",
)

st.subheader("Preview & export", divider="gray")

raw = _build_raw(
    title,
    description,
    base_path,
    samples_df,
    base_year,
    taux_sedimentation,
    coring_yr,
    nuclides_df,
    columns_df,
)

try:
    config = BuildConfig.from_dict(raw)
except (ValueError, KeyError) as e:
    st.error(f"Configuration is not valid yet: {e}", icon=":material/error:")
else:
    st.success(
        f"Valid — {len(config.samples)} sample(s), {len(config.nuclides)} nuclide(s), "
        f"{len(config.columns)} column(s).",
        icon=":material/check_circle:",
    )

    toml_text = config.to_toml()

    with st.expander("TOML preview", icon=":material/code:"):
        st.code(toml_text, language="toml")

    action_col1, action_col2 = st.columns(2)
    with action_col1:
        slug = "".join(c if c.isalnum() else "_" for c in config.title.lower()).strip("_")
        st.download_button(
            "Download build file",
            data=toml_text.encode("utf-8"),
            file_name=f"{slug or 'build'}.toml",
            mime="application/toml",
            icon=":material/download:",
            width="stretch",
        )
    with action_col2:
        load_clicked = st.button(
            "Load into app", icon=":material/rocket_launch:", width="stretch", type="primary"
        )
        if load_clicked and load_build_config(config):
            st.session_state["_build_file_key"] = ("editor", id(config))
            st.success("Loaded — see the Reports and Synthesis pages.")
