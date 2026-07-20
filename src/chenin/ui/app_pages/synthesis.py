import plotly.graph_objects as go
import streamlit as st

from chenin.g2k_parser import format_nuclide
from chenin.synthesis import SynthesisBuilder
from chenin.ui import state
from chenin.ui.components.dataframe_view_mode import df_view_mode_widget
from chenin.ui.components.export import export_dataframe

st.title("Synthesis")
st.caption("One row per sample: activities, uncertainties and depth.")

config = state.get_build_config()
reports = state.get_reports()

if config is None or not reports:
    st.info("Load a roadmap on the Roadmap page to build the synthesis.")
    st.stop()

with st.expander(f"Configuration — “{config.title}”", expanded=False):
    if config.description:
        st.caption(config.description)

    meta = config.metadata
    badges = []
    if meta.base_year is not None:
        badges.append(f":blue-badge[Base year: {meta.base_year:g}]")
    if meta.taux_sedimentation:
        badges.append(f":blue-badge[Sedimentation rate: {meta.taux_sedimentation:g}]")
    if meta.coring_yr is not None:
        badges.append(f":blue-badge[Coring year: {meta.coring_yr:g}]")
    if badges:
        st.markdown(" ".join(badges))
    else:
        st.caption("No age model configured — the Age column will be omitted.")

    st.markdown("**Nuclides**")
    for _key, nuclide in config.nuclides.items():
        peaks = ", ".join(f"`{format_nuclide(p.nuclide)}` @ {p.energy} keV" for p in nuclide.peaks)
        st.markdown(f"- {peaks}")

    st.markdown("**Columns**")
    for column in config.columns:
        source = (
            f"source = `{column.source}`"
            if column.source is not None
            else f"formula = `{column.formula}`"
        )
        st.markdown(f"- **{column.name}**: {source}")

try:
    df = SynthesisBuilder(config).build(reports)
except Exception as e:
    st.error(f"Failed to build the synthesis: {e}")
    st.stop()

state.store_synthesis(df)

activity_cols = [c for c in df.columns if c.startswith("Activite ")]
has_age = "Age" in df.columns
depth_top = df["Profondeur"]
depth_bot = df["Profondeur"] + df["Epaisseur"]
depth_mid = df["Profondeur"] + df["Epaisseur"] / 2


def _nuclide_name(activity_col: str) -> str:
    return activity_col.removeprefix("Activite ")


if not activity_cols:
    st.warning("The synthesis has no activity columns to visualise.")
    st.stop()

# ------------------------------- Core view -------------------------------------------#
st.subheader("Core", divider="gray")

color_col = st.selectbox(
    "Colour layers by",
    activity_cols,
    format_func=_nuclide_name,
    key="core_color",
)

core_col, legend_col = st.columns([1, 3])

with core_col:
    fig_core = go.Figure(
        go.Bar(
            x=["Core"] * len(df),
            y=df["Epaisseur"],
            base=depth_top,
            marker=dict(
                color=df[color_col],
                colorscale="Viridis",
                colorbar=dict(title=_nuclide_name(color_col)),
                line=dict(color="rgba(0,0,0,0.3)", width=1),
            ),
            customdata=list(zip(depth_top, depth_bot, df[color_col], strict=True)),
            hovertemplate=(
                "Layer %{customdata[0]:.1f}–%{customdata[1]:.1f} cm<br>"
                f"{_nuclide_name(color_col)}: %{{customdata[2]:.1f}} mBq/g<extra></extra>"
            ),
        )
    )
    fig_core.update_yaxes(autorange="reversed", title="Depth (cm)")
    fig_core.update_xaxes(showticklabels=False)
    fig_core.update_layout(height=520, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_core, width="stretch", key="core_chart")

with legend_col:
    st.caption(
        "Each band is a sample, from top (`depth_top`) to bottom (`depth_bot`). "
        "Colour encodes the chosen activity."
    )

    legend_cols = ["Profondeur", "Epaisseur", color_col] + (["Age"] if has_age else [])
    tmp_df = df[legend_cols].rename(columns={color_col: _nuclide_name(color_col)})

    st.dataframe(tmp_df, hide_index=True, width="stretch")

# ------------------------------- Depth profiles ---------------------------------------#
st.subheader("Profiles", divider="gray")

log_scale = st.toggle(
    "Log scale",
    key="profile_log_scale",
    help="Semi-log view — a straight line indicates a constant sedimentation rate "
    "(the classic ²¹⁰Pb CRS/CFCS diagnostic). Non-positive values are hidden.",
)

n_cols = 3
cols = st.columns(n_cols)
for i, activity_col in enumerate(activity_cols):
    name = _nuclide_name(activity_col)
    unc_col = f"Incertitude {name}"
    fig = go.Figure(
        go.Scatter(
            x=df[activity_col],
            y=depth_mid,
            mode="lines+markers",
            error_x=dict(array=df[unc_col]) if unc_col in df else None,
            name=name,
        )
    )
    fig.update_yaxes(autorange="reversed", title="Depth (cm)")
    fig.update_xaxes(title=f"{name} (mBq/g)", type="log" if log_scale else "linear")
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10), title=name)
    cols[i % n_cols].plotly_chart(fig, width="stretch", key=f"profile_{name}")

# ------------------------------- Age model ----------------------------------------------#
if has_age:
    st.subheader("Age model", divider="gray")

    fig_age = go.Figure(
        go.Scatter(x=df["Age"], y=df["Profondeur"], mode="lines+markers", marker=dict(size=8))
    )
    fig_age.update_yaxes(autorange="reversed", title="Depth (cm)")
    fig_age.update_xaxes(title="Age (yr)")
    fig_age.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_age, width="stretch", key="age_chart")

    if meta.taux_sedimentation:
        st.caption(f"Constant sedimentation rate: {meta.taux_sedimentation:g} cm/yr.")

# ------------------------------- Data quality --------------------------------------------#
st.subheader("Data quality", divider="gray")
st.caption("Relative uncertainty (1σ) per nuclide — flags low-count measurements.")

fig_qc = go.Figure()
for activity_col in activity_cols:
    name = _nuclide_name(activity_col)
    unc_col = f"Incertitude {name}"
    if unc_col not in df:
        continue
    relative_uncertainty = (df[unc_col] / df[activity_col]).abs() * 100
    fig_qc.add_trace(
        go.Scatter(x=relative_uncertainty, y=depth_mid, mode="lines+markers", name=name)
    )
fig_qc.update_yaxes(autorange="reversed", title="Depth (cm)")
fig_qc.update_xaxes(title="Relative uncertainty (%)")
fig_qc.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig_qc, width="stretch", key="qc_chart")

# ------------------------------- Table --------------------------------------------------#
st.subheader("Table", divider="gray")

with st.container(border=True):
    df_view_mode_widget(df, "synthesis", "table")

    # SERAC is reserved for the synthesis (it's an R age-depth modelling tool).
    export_dataframe(df, filename="synthesis", formats=("CSV", "Parquet", "SERAC"))
