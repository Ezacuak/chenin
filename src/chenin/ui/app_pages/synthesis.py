"""Synthesis page: pick reports, describe the core, build the output table.

Section 3 hosts five candidate designs for the column builder. They are genuine
alternatives, not mockups: all five produce the same object — a *schema* — which is
translated into real ``NuclideSpec``/``ColumnSpec`` objects and handed to the real
``SynthesisBuilder``. Whichever design wins is already wired to production code.
"""

import io
import json
import re
from importlib import resources

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from chenin.g2k_parser import format_nuclide
from chenin.synthesis import (
    BuildConfig,
    ColumnSpec,
    NuclideSpec,
    Peak,
    SampleSpec,
    SynthesisBuilder,
    contiguity_gaps,
    overlaps,
    slice_samples,
)
from chenin.synthesis.config import (
    _REF_PATTERN,  # reused so [Name] refs key exactly as the real template parser
    GEOMETRY_COLUMNS,
    _slug,
    parse_template,
)
from chenin.synthesis.measurement import Measurement
from chenin.synthesis.providers import (
    ACTIVITY_COL,
    ENERGY_COL,
    ENERGY_TOLERANCE,
    NUCLIDE_COL,
    UNCERTAINTY_COL,
    evaluate_formula,
)
from chenin.ui import state

_PALETTE = [
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#e87ba4",  # magenta
    "#008300",  # green
    "#4a3aa7",  # violet
    "#e34948",  # red
]

st.title("Synthesis")
st.caption("One row per sample: layer geometry, activities and uncertainties.")

st.warning(":material/bug_report: Work in progress")


# ===================================================================================== #
# ================================= Reports Selection ================================= #
# ===================================================================================== #
reports = state.get_reports()
if not reports:
    st.info("Load some reports in the Load data page to construct a synthesis here")
    st.stop()

st.subheader("1. Reports selection", divider="grey")

options = st.multiselect(
    "Select report(s) you want in your synthesis.",
    reports,
)

if not options:
    st.stop()

selected_reports = {name: reports[name] for name in options}

# ===================================================================================== #
# ================================= Nuclide Library =================================== #
# ===================================================================================== #
st.subheader("2. Nuclide Library", divider="gray")
st.caption("Reference peaks (keV) used to identify nuclides across reports.")

library = state.get_nuclide_library()

with st.sidebar:
    st.header("Nuclide library")

    uploaded_file = st.file_uploader(
        "Load library file", type=["json", "csv"], help="Upload a JSON or CSV file."
    )

    if uploaded_file is not None and st.button("Apply loaded file"):
        try:
            parsed: dict[str, list[float]] = {}

            if uploaded_file.name.endswith(".json"):
                for key, peaks in json.load(uploaded_file).items():
                    parsed[format_nuclide(key)] = sorted(float(p) for p in peaks)
            else:
                csv = pd.read_csv(uploaded_file)
                for _, row in csv.iterrows():
                    peaks_str = str(row["Peaks"])
                    peaks = [float(p.strip()) for p in peaks_str.split(",") if p.strip()]
                    parsed[format_nuclide(str(row["Nuclide"]))] = sorted(peaks)

            state.store_nuclide_library(parsed)
            st.success("Library loaded.")
            st.rerun()

        except ValueError as e:
            st.error(f"Format error in file: {e}")

    st.divider()

    if st.button("Reset to default"):
        state.store_nuclide_library(state.DEFAULT_NUCLIDE_LIBRARY.copy())
        st.rerun()

    st.download_button(
        "Download library (JSON)",
        data=json.dumps(library, indent=2),
        file_name="nuclide_library.json",
        mime="application/json",
        icon=":material/download:",
    )

with st.form("add_nuclide_form", clear_on_submit=True):
    st.subheader("Add / update nuclide")
    col1, col2 = st.columns([1, 2])

    with col1:
        nuclide_input = st.text_input("Nuclide name", placeholder="e.g., 210pb, pb-210")
    with col2:
        peaks_input = st.text_input("Energy peaks (keV)", placeholder="e.g., 46.5, 12.0")

    submitted = st.form_submit_button("Save to library")

    if submitted:
        if not nuclide_input or not peaks_input:
            st.warning("Please provide both a nuclide name and at least one peak.")
        else:
            try:
                canonical_name = format_nuclide(nuclide_input)
                peaks = [float(p.strip()) for p in peaks_input.split(",") if p.strip()]
                library[canonical_name] = sorted(peaks)
                state.store_nuclide_library(library)
                st.toast(f"Saved as **{canonical_name}**!")
                st.rerun()
            except ValueError as e:
                st.error(f"Input error: {e}")

# NOTE: Pour Anne-lise
st.info(":material/notification_settings: Anne-lise: On peut changer la librairie par default.")

with st.expander("Active library"):
    if not library:
        st.info("The library is currently empty. Add a nuclide above or upload a JSON/CSV file.")
    else:
        for nuc, peaks in list(library.items()):
            col_info, col_action = st.columns([5, 1])
            with col_info:
                peaks_formatted = ", ".join(f"{p:.2f}" for p in peaks)
                st.markdown(f"**{nuc}**: `{peaks_formatted}` keV")
                with col_action:
                    if st.button("Delete", key=f"del_{nuc}"):
                        del library[nuc]
                        state.store_nuclide_library(library)
                        st.rerun()

if not library:
    st.stop()


# ===================================================================================== #
# =================================== Core layers ===================================== #
# ===================================================================================== #
# G2K reports carry no depth. This is the one place the layer geometry is entered, and
# every builder concept below reads it from here.

L_REPORT = "Rapport"
L_SAMPLE = "Echantillon"
L_TOP = "Profondeur"
L_BOT = "Depth bot"
L_DBD = "DBD"
LAYER_COLUMNS = [L_REPORT, L_SAMPLE, L_TOP, L_BOT, L_DBD]


def _sample_name(report) -> str:
    """The sample name G2K recorded in section 1, falling back to the report key."""
    s1 = report["s1"]
    for column in s1.columns:
        if column.lower().startswith("nom de l") and "chantillon" in column.lower():
            value = str(s1.iloc[0][column]).strip()
            if value:
                return value
    return report.name


def _blank_layers(subset: dict) -> pd.DataFrame:
    """An empty layer table, one row per selected report."""
    return pd.DataFrame(
        {
            L_REPORT: list(subset),
            L_SAMPLE: [_sample_name(r) for r in subset.values()],
            L_TOP: pd.Series([None] * len(subset), dtype="float"),
            L_BOT: pd.Series([None] * len(subset), dtype="float"),
            L_DBD: pd.Series([None] * len(subset), dtype="float"),
        }
    )


def _generated_layers(subset: dict, *, start: float, thickness: float, by_name: bool):
    """Prefill the grid from the core's slicing rule (same code the CLI uses)."""
    samples = slice_samples(subset, start=start, thickness=thickness, use_name_index=by_name)
    depths = {s.report: s for s in samples}
    frame = _blank_layers(subset)
    frame[L_TOP] = [depths[name].depth_top for name in frame[L_REPORT]]
    frame[L_BOT] = [depths[name].depth_bot for name in frame[L_REPORT]]
    return frame


def _sync_layers(subset: dict) -> pd.DataFrame:
    """Keep the stored grid aligned with the current report selection.

    Depths already typed for a report are preserved when the selection changes; new
    reports arrive blank and de-selected ones drop out.
    """
    stored = state.get_layers()
    fresh = _blank_layers(subset)
    if stored is None or stored.empty:
        return fresh

    known = stored.set_index(L_REPORT)
    for column in (L_SAMPLE, L_TOP, L_BOT, L_DBD):
        if column not in known.columns:
            continue
        fresh[column] = [
            known.at[name, column] if name in known.index else fresh.at[i, column]
            for i, name in enumerate(fresh[L_REPORT])
        ]
    return fresh


def _layers_to_samples(layers: pd.DataFrame) -> tuple[list[SampleSpec], list[str]]:
    """Turn the grid into SampleSpecs, returning the rows that could not be used."""
    samples: list[SampleSpec] = []
    skipped: list[str] = []

    for row in layers.to_dict("records"):
        name = str(row[L_REPORT])
        top, bot = row.get(L_TOP), row.get(L_BOT)
        if top is None or bot is None or pd.isna(top) or pd.isna(bot):
            skipped.append(f"{name} (no depth)")
            continue
        if float(bot) <= float(top):
            skipped.append(f"{name} (bottom {bot} is not below top {top})")
            continue

        dbd = row.get(L_DBD)
        sample_code = str(row.get(L_SAMPLE) or "").strip() or name
        samples.append(
            SampleSpec(
                report=name,
                depth_top=float(top),
                depth_bot=float(bot),
                sample_code=sample_code,
                dbd=None if dbd is None or pd.isna(dbd) else float(dbd),
            )
        )

    return samples, skipped


st.subheader("3. Core layers", divider="grey")
st.caption(
    "Which report is which layer. G2K reports carry no depth, so this is the one place "
    "the core geometry is described."
)

st.session_state.setdefault("layers_version", 0)

with st.expander(":material/straighten: Generate depths from a slicing rule", expanded=True):
    gen_a, gen_b, gen_c = st.columns([1, 1, 2])
    with gen_a:
        gen_start = st.number_input("Start depth (cm)", value=0.0, step=0.5, key="gen_start")
    with gen_b:
        gen_thickness = st.number_input(
            "Slice thickness (cm)", value=0.5, min_value=0.01, step=0.1, key="gen_thickness"
        )
    with gen_c:
        gen_mode = st.radio(
            "Slice number",
            ["From the file name", "Sequential"],
            key="gen_mode",
            horizontal=True,
            help=(
                "'From the file name' reads the trailing number (NOI_S_13 → 13), so a core "
                "with unmeasured slices keeps its true depths. 'Sequential' stacks the "
                "selected reports contiguously."
            ),
        )

    if st.button("Fill the table", icon=":material/auto_fix_high:"):
        state.store_layers(
            _generated_layers(
                selected_reports,
                start=gen_start,
                thickness=gen_thickness,
                by_name=gen_mode == "From the file name",
            )
        )
        st.session_state.layers_version += 1  # reset the editor widget state
        st.rerun()

    st.caption("This only prefills the table — every cell stays editable afterwards.")

layers = st.data_editor(
    _sync_layers(selected_reports),
    key=f"layers_editor_{st.session_state.layers_version}",
    column_config={
        L_REPORT: st.column_config.TextColumn("Report", pinned=True),
        L_SAMPLE: st.column_config.TextColumn("Sample", help="Defaults to the G2K sample name."),
        L_TOP: st.column_config.NumberColumn("Depth top (cm)", format="%.2f"),
        L_BOT: st.column_config.NumberColumn("Depth bottom (cm)", format="%.2f"),
        L_DBD: st.column_config.NumberColumn("DBD (g/cm³)", format="%.3f"),
    },
    disabled=[L_REPORT],
    hide_index=True,
    width="stretch",
)
state.store_layers(layers)

samples, skipped = _layers_to_samples(layers)

if not samples:
    st.info("Enter a depth for at least one report — or use the generator above.")
    st.stop()

depth_min = min(s.depth_top for s in samples)
depth_max = max(s.depth_bot for s in samples)
st.caption(f"{len(samples)} layer(s) · {depth_min:g}–{depth_max:g} cm")

if skipped:
    st.warning("Excluded from the synthesis — " + "; ".join(skipped))

if collisions := overlaps(samples):
    st.error(
        "Overlapping layers: " + "; ".join(f"{a.report} and {b.report}" for a, b in collisions)
    )

if gaps := contiguity_gaps(samples):
    st.warning(
        ":material/info: Unmeasured intervals (fine for a partially measured core): "
        + ", ".join(f"{lo:g}–{hi:g} cm" for lo, hi in gaps)
    )


# ===================================================================================== #
# ================================= Synthesis Builder ================================= #
# ===================================================================================== #
st.subheader("4. Synthesis build", divider="grey")

st.warning(
    ":material/build: Five candidate designs for the column builder — try them and pick one."
)


# --- Shared plumbing ----------------------------------------------------------------- #
# Every concept produces the same thing: a *schema*, an ordered list of
#   {"name": str, "peaks": [(nuclide, energy), ...]}   -> measured (weighted mean)
#   {"name": str, "formula": "[A] - [B]"}              -> derived
#   {"name": str, "geometry": "depth_top"}             -> from the core-layer table
# which is translated into real specs and handed to the real SynthesisBuilder, so the
# preview is genuine output and not a mock.


def _peak_options(lib: dict[str, list[float]]) -> list[str]:
    """Every peak in the library as a flat 'NUC@energy' list."""
    return [f"{nuc}@{p:g}" for nuc in sorted(lib) for p in lib[nuc]]


def _parse_peak(option: str) -> tuple[str, float]:
    nuclide, _, energy = option.partition("@")
    return nuclide.strip(), float(energy)


def _geometry_item(field: str) -> dict:
    return {"name": GEOMETRY_COLUMNS[field], "geometry": field}


def _default_geometry_schema() -> list[dict]:
    return [_geometry_item(field) for field in GEOMETRY_COLUMNS]


def _excess_item() -> dict:
    return {"name": "PB-210ex", "formula": "=[PB-210] - [RA-226]"}


def _schema_to_specs(schema: list[dict]) -> tuple[dict[str, NuclideSpec], list[ColumnSpec]]:
    """Translate a prototype schema into the real spec objects."""
    nuclides: dict[str, NuclideSpec] = {}
    columns: list[ColumnSpec] = []
    for item in schema:
        key = _slug(item["name"])
        if item.get("geometry"):
            columns.append(ColumnSpec(key=key, name=item["name"], geometry=item["geometry"]))
        elif item.get("formula"):
            expr = item["formula"].lstrip("=").strip()
            formula = _REF_PATTERN.sub(lambda m: _slug(m.group(1)), expr)
            columns.append(ColumnSpec(key=key, name=item["name"], formula=formula))
        else:
            peaks = [Peak(nuclide=n, energy=e) for n, e in item["peaks"]]
            nuclides[key] = NuclideSpec(key=key, peaks=peaks)
            columns.append(ColumnSpec(key=key, name=item["name"], source=key))
    return nuclides, columns


def _build(schema: list[dict], subset: dict) -> pd.DataFrame:
    """Run the real builder over the current schema and core layers."""
    if not any(item.get("geometry") for item in schema):
        schema = _default_geometry_schema() + schema

    nuclides, columns = _schema_to_specs(schema)
    config = BuildConfig(
        title="Synthesis",
        description=None,
        samples=samples,
        nuclides=nuclides,
        columns=columns,
    )
    return SynthesisBuilder(config).build(subset)


def _activity_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith("Activite ")]


def _nuclide_name(activity_col: str) -> str:
    return activity_col.removeprefix("Activite ")


def _depth_profile(df: pd.DataFrame, key: str) -> None:
    """Activity against mid-depth, the standard way to read a core."""
    activity_cols = _activity_columns(df)
    if not activity_cols or "Profondeur" not in df:
        st.caption("Nothing to plot yet.")
        return

    mid_depth = df["Profondeur"] + df["Epaisseur"] / 2
    log_scale = st.toggle(
        "Log scale",
        key=f"{key}_log",
        help="A straight line on a semi-log plot indicates a constant sedimentation rate "
        "(the classic ²¹⁰Pb CFCS diagnostic). Non-positive values are hidden.",
    )

    fig = go.Figure()
    for i, col in enumerate(activity_cols):
        name = _nuclide_name(col)
        unc = f"Incertitude {name}"
        fig.add_trace(
            go.Scatter(
                x=df[col],
                y=mid_depth,
                mode="lines+markers",
                name=name,
                error_x=dict(array=df[unc]) if unc in df else None,
                line=dict(color=_PALETTE[i % len(_PALETTE)], width=2),
            )
        )
    fig.update_yaxes(autorange="reversed", title="Depth (cm)")
    fig.update_xaxes(title="Activity (mBq/g)", type="log" if log_scale else "linear")
    fig.update_layout(height=460, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width="stretch", key=f"{key}_profile")


def _core_figure(df: pd.DataFrame, color_col: str) -> go.Figure:
    """The core as a stack of coloured bands, one per layer."""
    depth_bot = df["Profondeur"] + df["Epaisseur"]
    fig = go.Figure(
        go.Bar(
            x=["Core"] * len(df),
            y=df["Epaisseur"],
            base=df["Profondeur"],
            marker=dict(
                color=df[color_col],
                colorscale="Viridis",
                colorbar=dict(title=_nuclide_name(color_col)),
                line=dict(color="rgba(0,0,0,0.3)", width=1),
            ),
            customdata=list(zip(df["Profondeur"], depth_bot, df[color_col], strict=True)),
            hovertemplate=(
                "Layer %{customdata[0]:.1f}–%{customdata[1]:.1f} cm<br>"
                f"{_nuclide_name(color_col)}: %{{customdata[2]:.1f}} mBq/g<extra></extra>"
            ),
        )
    )
    fig.update_yaxes(autorange="reversed", title="Depth (cm)")
    fig.update_xaxes(showticklabels=False)
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=10, b=10))
    return fig


def _render_preview(schema: list[dict], key: str) -> None:
    """Shared result panel, identical across concepts so they compare fairly."""
    st.divider()
    st.markdown("##### Synthesis preview")

    measured = [item for item in schema if not item.get("geometry")]
    if not measured:
        st.warning("No activity column defined yet — add at least one above.")
        return

    try:
        df = _build(schema, selected_reports)
    except (ValueError, SyntaxError) as e:
        st.error(f"Could not build the synthesis: {e}")
        return

    st.caption(
        f"{len(df)} row(s) · {len(measured)} activity column(s) → {len(df.columns)} output columns."
    )

    tab_table, tab_profile = st.tabs(["Table", "Depth profile"])
    with tab_table:
        st.dataframe(df, hide_index=True, key=f"{key}_df", width="stretch")
    with tab_profile:
        _depth_profile(df, key)

    state.store_synthesis(df)


def _peak_inventory(subset: dict) -> pd.DataFrame:
    """Every gamma line actually present in the selected reports.

    Energies drift slightly between reports, so lines within ``ENERGY_TOLERANCE`` of
    each other are clustered into a single row — the same tolerance the resolver uses
    when matching a configured peak.
    """
    frames = []
    for name, report in subset.items():
        s3 = report["s3"][[NUCLIDE_COL, ENERGY_COL, ACTIVITY_COL, UNCERTAINTY_COL]].copy()
        s3["report"] = name
        frames.append(s3)

    raw = pd.concat(frames, ignore_index=True)
    raw[ENERGY_COL] = pd.to_numeric(raw[ENERGY_COL], errors="coerce")
    raw[ACTIVITY_COL] = pd.to_numeric(raw[ACTIVITY_COL], errors="coerce")
    raw[UNCERTAINTY_COL] = pd.to_numeric(raw[UNCERTAINTY_COL], errors="coerce")
    raw = raw.dropna(subset=[NUCLIDE_COL, ENERGY_COL, ACTIVITY_COL])

    rows = []
    for nuclide, group in raw.groupby(NUCLIDE_COL, sort=True):
        group = group.sort_values(ENERGY_COL)
        cluster: list = []
        for record in group.to_dict("records"):
            if cluster and record[ENERGY_COL] - cluster[0][ENERGY_COL] > ENERGY_TOLERANCE:
                rows.append(_inventory_row(nuclide, cluster, len(subset)))
                cluster = []
            cluster.append(record)
        if cluster:
            rows.append(_inventory_row(nuclide, cluster, len(subset)))

    inventory = pd.DataFrame(rows)
    return inventory.sort_values(
        ["Coverage", "Nuclide"], ascending=[False, True], ignore_index=True
    )


def _inventory_row(nuclide: str, cluster: list[dict], total: int) -> dict:
    energies = [c[ENERGY_COL] for c in cluster]
    activities = pd.Series([c[ACTIVITY_COL] for c in cluster])
    uncertainties = pd.Series([c[UNCERTAINTY_COL] for c in cluster])
    return {
        "Nuclide": nuclide,
        "Energy": sum(energies) / len(energies),
        "Coverage": len({c["report"] for c in cluster}),
        "Total": total,
        "Mean activity": activities.mean(),
        "Rel. uncertainty": (uncertainties / activities).abs().median() * 100,
    }


def _validate_formula(expr: str, schema: list[dict]) -> str | None:
    """Check a formula against the real evaluator; return an error message or None."""
    nuclides, _ = _schema_to_specs([i for i in schema if not i.get("geometry")])
    dummy = {k: Measurement(1.0, 0.1) for k in nuclides}
    parsed = _REF_PATTERN.sub(lambda m: _slug(m.group(1)), expr.lstrip("=").strip())
    try:
        evaluate_formula(parsed, dummy)
    except (ValueError, SyntaxError) as e:
        return str(e)
    return None


def _formula_form(schema: list[dict], key: str) -> dict | None:
    """A live-validated derived-column form. Returns the new schema item, if any."""
    with st.form(f"{key}_formula", clear_on_submit=True):
        st.markdown("**Add a derived column**")
        col_name, col_expr = st.columns([1, 2])
        with col_name:
            name = st.text_input("Column name", placeholder="e.g. PB-210ex")
        with col_expr:
            expr = st.text_input("Expression", placeholder="=[PB-210] - [RA-226]")

        if not st.form_submit_button("Add column"):
            return None

        if not name or not expr:
            st.warning("Provide both a name and an expression.")
            return None

        if error := _validate_formula(expr, schema):
            st.error(f"Invalid formula: {error}")
            return None

        return {"name": name, "formula": expr}


st.caption(
    "All five designs define the same object — the column schema — and share the same "
    f"preview, built from the {len(selected_reports)} selected report(s) and the layers above."
)

tab_catalog, tab_wizard, tab_peaks, tab_template, tab_canvas = st.tabs(
    [
        ":material/table_rows: Data catalog",
        ":material/conversion_path: Guided wizard",
        ":material/graphic_eq: Peak-first",
        ":material/grid_on: Template editor",
        ":material/layers: Core canvas",
    ]
)

# ------------------------------------------------------------------------------------- #
# A — Interactive data catalog (matrix + presets)
# ------------------------------------------------------------------------------------- #
with tab_catalog:
    st.markdown(
        "One editable matrix holding **every** output column, geometry included, plus "
        "one-click lab presets. The **Method** cell is editable: `NUC@energy` "
        "(`,`-separated for a weighted mean) or an `=` formula."
    )

    _PRESETS = {
        "Standard 210Pb / 137Cs": ["PB-210", "CS-137", "RA-226", "PB-210ex"],
        "Everything": None,  # all rows
        "SERAC ready": ["PB-210ex", "CS-137"],
    }

    def _default_catalog(lib: dict[str, list[float]], subset: dict) -> pd.DataFrame:
        coverage = _peak_inventory(subset)
        seen = {
            (row["Nuclide"], round(row["Energy"], 1)): row["Coverage"]
            for row in coverage.to_dict("records")
        }

        def _covered(nuc: str) -> str:
            hits = [
                next(
                    (
                        c
                        for (n, e), c in seen.items()
                        if n == nuc and abs(e - p) <= ENERGY_TOLERANCE
                    ),
                    0,
                )
                for p in lib[nuc]
            ]
            return f"{max(hits, default=0)}/{len(subset)}"

        rows = [
            {
                "Select": True,
                "Column": name,
                "Category": "Geometry",
                "Method": "from 3. Core layers",
                "Coverage": f"{len(samples)}/{len(subset)}",
            }
            for name in GEOMETRY_COLUMNS.values()
        ]
        rows += [
            {
                "Select": nuc in ("PB-210", "CS-137", "RA-226"),
                "Column": nuc,
                "Category": "Measured",
                "Method": ", ".join(f"{nuc}@{p:g}" for p in lib[nuc]),
                "Coverage": _covered(nuc),
            }
            for nuc in sorted(lib)
        ]
        rows.append(
            {
                "Select": True,
                "Column": "PB-210ex",
                "Category": "Derived",
                "Method": "=[PB-210] - [RA-226]",
                "Coverage": "—",
            }
        )
        return pd.DataFrame(rows)

    st.session_state.setdefault("c1_catalog", _default_catalog(library, selected_reports))
    st.session_state.setdefault("c1_version", 0)

    st.markdown("**Quick presets**")
    with st.container(horizontal=True):
        for label, wanted in _PRESETS.items():
            if st.button(label, key=f"c1_preset_{label}"):
                cat = st.session_state.c1_catalog.copy()
                keep_geometry = cat["Category"] == "Geometry"
                cat["Select"] = (
                    True if wanted is None else (cat["Column"].isin(wanted) | keep_geometry)
                )
                st.session_state.c1_catalog = cat
                st.session_state.c1_version += 1  # reset the editor widget state
                st.rerun()
        if st.button("Reset catalog", key="c1_reset"):
            st.session_state.c1_catalog = _default_catalog(library, selected_reports)
            st.session_state.c1_version += 1
            st.rerun()

    edited = st.data_editor(
        st.session_state.c1_catalog,
        key=f"c1_editor_{st.session_state.c1_version}",
        column_config={
            "Select": st.column_config.CheckboxColumn("Include", default=False),
            "Column": st.column_config.TextColumn("Column name"),
            "Category": st.column_config.TextColumn("Kind"),
            "Method": st.column_config.TextColumn("Peaks / formula", width="medium"),
            "Coverage": st.column_config.TextColumn(
                "Coverage", help="Reports actually containing this line, out of those selected."
            ),
        },
        disabled=["Category", "Coverage"],
        hide_index=True,
        num_rows="dynamic",
        width="stretch",
    )

    _GEOMETRY_BY_NAME = {name: field for field, name in GEOMETRY_COLUMNS.items()}

    catalog_schema: list[dict] = []
    catalog_error: str | None = None
    for row in edited[edited["Select"].fillna(False)].to_dict("records"):
        name = str(row.get("Column") or "").strip()
        method = str(row.get("Method") or "").strip()
        if not name or not method:
            continue
        if name in _GEOMETRY_BY_NAME:
            catalog_schema.append(_geometry_item(_GEOMETRY_BY_NAME[name]))
            continue
        if method.startswith("="):
            catalog_schema.append({"name": name, "formula": method})
            continue
        try:
            peaks = [_parse_peak(p) for p in method.split(",") if p.strip()]
        except ValueError:
            catalog_error = f"row '{name}': method must be NUC@energy or an = formula"
            continue
        catalog_schema.append({"name": name, "peaks": peaks})

    if catalog_error:
        st.error(catalog_error)

    _render_preview(catalog_schema, "c1")

# ------------------------------------------------------------------------------------- #
# B — Guided wizard with live depth profile
# ------------------------------------------------------------------------------------- #
with tab_wizard:
    st.markdown("A stepped flow ending in a live depth profile and core view.")

    step_geom, step_nuc, step_derived, step_out = st.tabs(
        ["1. Layers", "2. Nuclides", "3. Derived", "4. Result"]
    )

    with step_geom:
        st.markdown("##### Core layers")
        st.caption("Entered once in section 3 above — this is a recap.")

        recap_a, recap_b, recap_c = st.columns(3)
        recap_a.metric("Layers", len(samples))
        recap_b.metric("Depth range", f"{depth_min:g}–{depth_max:g} cm")
        recap_c.metric("Excluded reports", len(skipped))

        if skipped:
            st.warning("Fix these in section 3 to include them: " + "; ".join(skipped))
        elif gaps:
            st.info(f"{len(gaps)} unmeasured interval(s) — expected on a partially measured core.")
        else:
            st.success("Every selected report has a layer.")

    with step_nuc:
        picked = st.multiselect(
            "Nuclides to measure",
            sorted(library),
            default=[n for n in ("PB-210", "CS-137", "RA-226") if n in library],
            key="c4_nuclides",
        )

    with step_derived:
        want_excess = st.toggle("Add PB-210ex", value=True, key="c4_excess")
        st.text_input(
            "Formula", value="=[PB-210] - [RA-226]", key="c4_formula", disabled=not want_excess
        )

    wizard_schema = [{"name": n, "peaks": [(n, p) for p in library[n]]} for n in picked]
    if want_excess and {"PB-210", "RA-226"} <= set(picked):
        wizard_schema.append({"name": "PB-210ex", "formula": st.session_state.c4_formula})
    elif want_excess and picked:
        with step_derived:
            st.info("PB-210ex needs both `PB-210` and `RA-226` selected in step 2.")

    with step_out:
        if not wizard_schema:
            st.warning("Pick at least one nuclide in step 2.")
        else:
            try:
                wiz_df = _build(wizard_schema, selected_reports)
            except (ValueError, SyntaxError) as e:
                st.error(f"Could not build the synthesis: {e}")
            else:
                state.store_synthesis(wiz_df)
                activity_cols = _activity_columns(wiz_df)

                col_table, col_chart = st.columns([3, 2])
                with col_table:
                    st.markdown("**Table**")
                    st.dataframe(wiz_df, hide_index=True, key="c4_table", width="stretch")
                    _depth_profile(wiz_df, "c4")

                with col_chart:
                    st.markdown("**Core**")
                    color_col = st.selectbox(
                        "Colour layers by",
                        activity_cols,
                        format_func=_nuclide_name,
                        key="c4_color",
                    )
                    st.plotly_chart(_core_figure(wiz_df, color_col), width="stretch", key="c4_core")

# ------------------------------------------------------------------------------------- #
# C — Peak-first: start from what the reports actually contain
# ------------------------------------------------------------------------------------- #
with tab_peaks:
    st.markdown(
        "Every gamma line **actually present** in the selected reports, with its coverage. "
        "Tick the lines you want; lines sharing a **Column** name are combined into one "
        "weighted mean — that is how ²²⁶Ra is built from its ²¹⁴Pb / ²¹⁴Bi progeny."
    )

    inventory = _peak_inventory(selected_reports)

    only_complete = st.toggle("Only lines present in every report", value=False, key="c5_complete")
    complete = inventory["Coverage"] == len(selected_reports)
    shown = inventory[complete] if only_complete else inventory

    default_lines = {"PB-210", "CS-137", "PB-214", "BI-214", "AM-241"}
    editable = shown.assign(
        Select=shown["Nuclide"].isin(default_lines) & (shown["Coverage"] > 0),
        Column=shown["Nuclide"],
    )[["Select", "Nuclide", "Energy", "Coverage", "Mean activity", "Rel. uncertainty", "Column"]]

    picked_lines = st.data_editor(
        editable,
        key="c5_editor",
        column_config={
            "Select": st.column_config.CheckboxColumn("Use", default=False),
            "Nuclide": st.column_config.TextColumn("Nuclide"),
            "Energy": st.column_config.NumberColumn("Energy (keV)", format="%.2f"),
            "Coverage": st.column_config.ProgressColumn(
                "Coverage",
                min_value=0,
                max_value=len(selected_reports),
                format="%d",
                help="Reports containing this line.",
            ),
            "Mean activity": st.column_config.NumberColumn("Mean (mBq/g)", format="%.1f"),
            "Rel. uncertainty": st.column_config.NumberColumn("1σ (%)", format="%.1f%%"),
            "Column": st.column_config.TextColumn(
                "Goes into column",
                help="Lines sharing a name are combined into one weighted mean.",
            ),
        },
        disabled=["Nuclide", "Energy", "Coverage", "Mean activity", "Rel. uncertainty"],
        hide_index=True,
        width="stretch",
    )

    grouped: dict[str, list[tuple[str, float]]] = {}
    for row in picked_lines[picked_lines["Select"].fillna(False)].to_dict("records"):
        column = str(row.get("Column") or row["Nuclide"]).strip()
        if column:
            grouped.setdefault(column, []).append((row["Nuclide"], float(row["Energy"])))

    peaks_schema = [{"name": name, "peaks": peaks} for name, peaks in grouped.items()]

    st.session_state.setdefault("c5_derived", [])
    if item := _formula_form(peaks_schema, "c5"):
        st.session_state.c5_derived.append(item)
        st.rerun()

    for i, item in enumerate(st.session_state.c5_derived):
        with st.container(border=True, horizontal=True):
            st.markdown(f"**{item['name']}** — :gray[{item['formula']}]")
            if st.button(":material/delete:", key=f"c5_del_{i}"):
                st.session_state.c5_derived.pop(i)
                st.rerun()

    _render_preview(peaks_schema + st.session_state.c5_derived, "c5")

# ------------------------------------------------------------------------------------- #
# D — Template spreadsheet editor: edit the real artefact
# ------------------------------------------------------------------------------------- #
with tab_template:
    st.markdown(
        "Edit the **synthesis template** itself — the two-row CSV the lab saves and reuses "
        "on the next core. The header row holds column names, the single row below holds "
        "each method (`NUC@energy`, `;`-separated, or an `=` formula)."
    )

    def _template_to_schema(nuclides: dict, columns: dict) -> list[dict]:
        """Inverse of _schema_to_specs, for a parsed template.

        ``parse_template`` slugifies formula references (``[PB-210]`` -> ``pb_210``);
        they are turned back into display references here so a downloaded template
        reads the way the lab wrote it, not the way the parser stores it.
        """
        display = {key: column["name"] for key, column in columns.items()}

        schema = []
        for key, column in columns.items():
            if key in nuclides:
                peaks = [(p["nuclide"], p["energy"]) for p in nuclides[key]["peaks"]]
                schema.append({"name": column["name"], "peaks": peaks})
            else:
                formula = re.sub(
                    r"[A-Za-z_][A-Za-z0-9_]*",
                    lambda m: f"[{display[m.group()]}]" if m.group() in display else m.group(),
                    column["formula"],
                )
                schema.append({"name": column["name"], "formula": f"={formula}"})
        return schema

    def _schema_to_row(schema: list[dict]) -> dict[str, str]:
        row = {}
        for item in schema:
            if item.get("formula"):
                row[item["name"]] = item["formula"]
            else:
                row[item["name"]] = "; ".join(f"{n}@{e:g}" for n, e in item["peaks"])
        return row

    def _parse_default():
        """The packaged lab template, read the same way BuildConfig.from_template reads it."""
        ref = resources.files("chenin.synthesis") / "default_template.csv"
        with resources.as_file(ref) as path:
            return parse_template(path)

    st.session_state.setdefault("c6_schema", _template_to_schema(*_parse_default()))

    ctl_load, ctl_upload, ctl_download = st.columns([1, 2, 1])

    with ctl_load:
        if st.button("Load lab default", icon=":material/restart_alt:", key="c6_default"):
            st.session_state.c6_schema = _template_to_schema(*_parse_default())
            st.rerun()

    with ctl_upload:
        upload = st.file_uploader("Load a template CSV", type=["csv"], key="c6_upload")
        if upload is not None and st.button("Apply template", key="c6_apply"):
            try:
                st.session_state.c6_schema = _template_to_schema(*parse_template(upload))
            except ValueError as e:
                st.error(f"Invalid template: {e}")
            else:
                st.rerun()

    template_row = _schema_to_row(st.session_state.c6_schema)

    with ctl_download:
        buffer = io.StringIO()
        pd.DataFrame([template_row]).to_csv(buffer, index=False)
        st.download_button(
            "Download",
            data=buffer.getvalue(),
            file_name="synthesis_template.csv",
            mime="text/csv",
            icon=":material/download:",
            key="c6_download",
        )

    st.markdown("**Template**")
    edited_row = st.data_editor(
        pd.DataFrame([template_row]),
        key="c6_editor",
        num_rows="fixed",
        hide_index=True,
        width="stretch",
    )

    add_name, add_method, add_button = st.columns([1, 2, 1])
    with add_name:
        new_name = st.text_input("New column", placeholder="e.g. TH-234", key="c6_name")
    with add_method:
        new_method = st.selectbox(
            "Method",
            [""] + _peak_options(library),
            key="c6_method",
            help="Pick a library peak, or add the column and type any method in the grid.",
        )
    with add_button:
        st.markdown("")
        if st.button("Add column", key="c6_add", width="stretch"):
            if not new_name:
                st.warning("Name the column first.")
            else:
                nuclide, energy = (
                    _parse_peak(new_method) if new_method else (format_nuclide(new_name), 0.0)
                )
                st.session_state.c6_schema.append({"name": new_name, "peaks": [(nuclide, energy)]})
                st.rerun()

    # The grid is the source of truth: re-parse it through the real template parser so
    # what the preview builds is exactly what the downloaded CSV would rebuild.
    buffer = io.StringIO()
    edited_row.to_csv(buffer, index=False)
    buffer.seek(0)
    buffer.name = "template.csv"

    try:
        template_schema = _template_to_schema(*parse_template(buffer))
    except ValueError as e:
        st.error(f"Invalid template: {e}")
        template_schema = []

    _render_preview(template_schema, "c6")

# ------------------------------------------------------------------------------------- #
# E — Core stratigraphy canvas: geometry and chemistry side by side
# ------------------------------------------------------------------------------------- #
with tab_canvas:
    st.markdown(
        "The core is the primary object. Click a band to see the raw section-3 lines "
        "behind its numbers — a suspect layer is one click from its evidence."
    )

    with st.expander(":material/tune: Columns", expanded=False):
        canvas_picked = st.multiselect(
            "Nuclides",
            sorted(library),
            default=[n for n in ("PB-210", "CS-137", "RA-226") if n in library],
            key="c7_nuclides",
        )
        st.session_state.setdefault("c7_derived", [_excess_item()])

        canvas_schema = [{"name": n, "peaks": [(n, p) for p in library[n]]} for n in canvas_picked]

        if item := _formula_form(canvas_schema, "c7"):
            st.session_state.c7_derived.append(item)
            st.rerun()

        for i, item in enumerate(st.session_state.c7_derived):
            with st.container(border=True, horizontal=True):
                st.markdown(f"**{item['name']}** — :gray[{item['formula']}]")
                if st.button(":material/delete:", key=f"c7_del_{i}"):
                    st.session_state.c7_derived.pop(i)
                    st.rerun()

    usable_derived = [
        item
        for item in st.session_state.c7_derived
        if not _validate_formula(item["formula"], canvas_schema + [item])
    ]
    canvas_schema = canvas_schema + usable_derived

    if dropped := len(st.session_state.c7_derived) - len(usable_derived):
        st.caption(f":orange[{dropped} derived column(s) hidden — their inputs are not selected.]")

    if not canvas_schema:
        st.warning("Pick at least one nuclide above.")
    else:
        try:
            canvas_df = _build(canvas_schema, selected_reports)
        except (ValueError, SyntaxError) as e:
            st.error(f"Could not build the synthesis: {e}")
        else:
            state.store_synthesis(canvas_df)

            col_core, col_detail = st.columns([2, 3])

            with col_core:
                color_col = st.selectbox(
                    "Colour layers by",
                    _activity_columns(canvas_df),
                    format_func=_nuclide_name,
                    key="c7_color",
                )
                event = st.plotly_chart(
                    _core_figure(canvas_df, color_col),
                    width="stretch",
                    key="c7_core",
                    on_select="rerun",
                    selection_mode="points",
                )

            with col_detail:
                points = event.selection["points"] if event and event.selection else []
                if not points:
                    st.info("Click a band in the core to inspect that layer.")
                    st.dataframe(canvas_df, hide_index=True, key="c7_table", width="stretch")
                else:
                    index = points[0]["point_index"]
                    row = canvas_df.iloc[index]
                    depth_bot = row["Profondeur"] + row["Epaisseur"]
                    st.markdown(
                        f"##### {row['Echantillon']} · {row['Profondeur']:g}–{depth_bot:g} cm"
                    )

                    st.markdown("**Computed columns**")
                    st.dataframe(
                        pd.DataFrame(
                            [
                                {
                                    "Column": _nuclide_name(c),
                                    "Activity (mBq/g)": row[c],
                                    "1σ": row.get(f"Incertitude {_nuclide_name(c)}"),
                                }
                                for c in _activity_columns(canvas_df)
                            ]
                        ),
                        hide_index=True,
                        width="stretch",
                    )

                    st.markdown("**Raw section 3**")
                    report_key = next(
                        (s.report for s in samples if s.sample_code == row["Echantillon"]), None
                    )
                    if report_key in selected_reports:
                        st.dataframe(
                            selected_reports[report_key]["s3"],
                            hide_index=True,
                            width="stretch",
                            height=280,
                        )
                    else:
                        st.caption("No report is attached to this layer.")
