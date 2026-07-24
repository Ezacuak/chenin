import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from chenin.g2k_parser import format_nuclide
from chenin.ui import state

# Categorical palette (fixed hue order, CVD-safe on adjacent pairs).
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
st.caption("One row per sample: activities, uncertainties and depth.")

st.warning(":material/bug_report: Work in progress")


# config = state.get_build_config()

# ===================================================================================== #
# ================================= Reports Selection ================================= #
# ===================================================================================== #
st.subheader("1. Reports selection", divider="grey")

reports = state.get_reports()

options = st.multiselect(
    "Select report(s) you want in your synthesis.",
    reports,
)

if not options:
    st.stop()

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

    st.divider()

    st.subheader("Export")
    st.download_button(
        "Download library (JSON)",
        data=json.dumps(library, indent=2),
        file_name="nuclide_library.json",
        mime="application/json",
        icon=":material/download:",
    )

tab_manage, tab_viewer = st.tabs(["Manage library", "Spectrum viewer"])

with tab_manage:
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

    st.divider()

    st.markdown("##### Active library")

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

with tab_viewer:
    st.warning(":material/timer: Comming soon !")

    # st.subheader("Gamma-ray peak spectrum", divider="gray")

    # if not library:
    #     st.info("No nuclides in the library yet. Add some in the Manage tab.")
    # else:
    #     nuclide_names = sorted(library.keys())

    #     selected = st.multiselect(
    #         "Nuclides to display",
    #         options=nuclide_names,
    #         default=nuclide_names,
    #     )

    #     col_a, col_b = st.columns([1, 1])
    #     with col_a:
    #         log_x = st.checkbox("Log scale (energy axis)", value=False)
    #     with col_b:
    #         sort_mode = st.radio("Order rows by", ["Name", "Lowest energy peak"], horizontal=True)

    #     if not selected:
    #         st.warning("Select at least one nuclide to plot.")
    #     else:
    #         if sort_mode == "Lowest energy peak":
    #             ordered = sorted(
    #                 selected,
    #                 key=lambda n: min(library[n]) if library[n] else float("inf"),
    #             )
    #         else:
    #             ordered = sorted(selected)

    #         # Color follows the nuclide, assigned over the full library so toggling
    #         # the selection never repaints the nuclides that stay on screen.
    #         color_map = {
    #             nuc: _PALETTE[i % len(_PALETTE)] for i, nuc in enumerate(sorted(library.keys()))
    #         }

    #         fig = go.Figure()

    #         for nuc in ordered:
    #             peaks = library[nuc]
    #             if not peaks:
    #                 continue
    #             fig.add_trace(
    #                 go.Scatter(
    #                     x=peaks,
    #                     y=[nuc] * len(peaks),
    #                     mode="markers",
    #                     marker=dict(
    #                         symbol="line-ns", size=22, line=dict(width=2, color=color_map[nuc])
    #                     ),
    #                     name=nuc,
    #                     hovertemplate="<b>%{y}</b><br>%{x:.2f} keV<extra></extra>",
    #                     showlegend=False,
    #                 )
    #             )

    #         fig.update_layout(
    #             height=max(320, 40 * len(ordered)),
    #             xaxis_title="Energy (keV)",
    #             yaxis_title="Nuclide",
    #             xaxis_type="log" if log_x else "linear",
    #             margin=dict(l=10, r=10, t=10, b=10),
    #             yaxis=dict(categoryorder="array", categoryarray=ordered),
    #             hovermode="closest",
    #         )
    #         st.plotly_chart(fig, width="stretch")

    #         with st.expander("Peak table"):
    #             rows = [
    #                 {"Nuclide": nuc, "Energy (keV)": p} for nuc in ordered for p in library[nuc]
    #             ]
    #             st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


# ===================================================================================== #


# if config is None or not reports:
#     st.info("Load a roadmap on the Roadmap page to build the synthesis.")
#     st.stop()

# with st.expander(f"Configuration — “{config.title}”", expanded=False):
#     if config.description:
#         st.caption(config.description)

#     meta = config.metadata
#     badges = []
#     if meta.base_year is not None:
#         badges.append(f":blue-badge[Base year: {meta.base_year:g}]")
#     if meta.taux_sedimentation:
#         badges.append(f":blue-badge[Sedimentation rate: {meta.taux_sedimentation:g}]")
#     if meta.coring_yr is not None:
#         badges.append(f":blue-badge[Coring year: {meta.coring_yr:g}]")
#     if badges:
#         st.markdown(" ".join(badges))
#     else:
#         st.caption("No age model configured — the Age column will be omitted.")

#     st.markdown("**Nuclides**")
#     for _key, nuclide in config.nuclides.items():
#         peaks = ", ".join(f"`{format_nuclide(p.nuclide)}` @ {p.energy} keV" for p in nuclide.peaks)
#         st.markdown(f"- {peaks}")

#     st.markdown("**Columns**")
#     for column in config.columns:
#         source = (
#             f"source = `{column.source}`"
#             if column.source is not None
#             else f"formula = `{column.formula}`"
#         )
#         st.markdown(f"- **{column.name}**: {source}")

# try:
#     df = SynthesisBuilder(config).build(reports)
# except Exception as e:
#     st.error(f"Failed to build the synthesis: {e}")
#     st.stop()

# state.store_synthesis(df)

# activity_cols = [c for c in df.columns if c.startswith("Activite ")]
# has_age = "Age" in df.columns
# depth_top = df["Profondeur"]
# depth_bot = df["Profondeur"] + df["Epaisseur"]
# depth_mid = df["Profondeur"] + df["Epaisseur"] / 2


# def _nuclide_name(activity_col: str) -> str:
#     return activity_col.removeprefix("Activite ")


# if not activity_cols:
#     st.warning("The synthesis has no activity columns to visualise.")
#     st.stop()

# # ------------------------------- Core view -------------------------------------------#
# st.subheader("Core", divider="gray")

# color_col = st.selectbox(
#     "Colour layers by",
#     activity_cols,
#     format_func=_nuclide_name,
#     key="core_color",
# )

# core_col, legend_col = st.columns([1, 3])

# with core_col:
#     fig_core = go.Figure(
#         go.Bar(
#             x=["Core"] * len(df),
#             y=df["Epaisseur"],
#             base=depth_top,
#             marker=dict(
#                 color=df[color_col],
#                 colorscale="Viridis",
#                 colorbar=dict(title=_nuclide_name(color_col)),
#                 line=dict(color="rgba(0,0,0,0.3)", width=1),
#             ),
#             customdata=list(zip(depth_top, depth_bot, df[color_col], strict=True)),
#             hovertemplate=(
#                 "Layer %{customdata[0]:.1f}–%{customdata[1]:.1f} cm<br>"
#                 f"{_nuclide_name(color_col)}: %{{customdata[2]:.1f}} mBq/g<extra></extra>"
#             ),
#         )
#     )
#     fig_core.update_yaxes(autorange="reversed", title="Depth (cm)")
#     fig_core.update_xaxes(showticklabels=False)
#     fig_core.update_layout(height=520, margin=dict(l=10, r=10, t=10, b=10))
#     st.plotly_chart(fig_core, width="stretch", key="core_chart")

# with legend_col:
#     st.caption(
#         "Each band is a sample, from top (`depth_top`) to bottom (`depth_bot`). "
#         "Colour encodes the chosen activity."
#     )

#     legend_cols = ["Profondeur", "Epaisseur", color_col] + (["Age"] if has_age else [])
#     tmp_df = df[legend_cols].rename(columns={color_col: _nuclide_name(color_col)})

#     st.dataframe(tmp_df, hide_index=True, width="stretch")

# # ------------------------------- Depth profiles ---------------------------------------#
# st.subheader("Profiles", divider="gray")

# log_scale = st.toggle(
#     "Log scale",
#     key="profile_log_scale",
#     help="Semi-log view — a straight line indicates a constant sedimentation rate "
#     "(the classic ²¹⁰Pb CRS/CFCS diagnostic). Non-positive values are hidden.",
# )

# n_cols = 3
# cols = st.columns(n_cols)
# for i, activity_col in enumerate(activity_cols):
#     name = _nuclide_name(activity_col)
#     unc_col = f"Incertitude {name}"
#     fig = go.Figure(
#         go.Scatter(
#             x=df[activity_col],
#             y=depth_mid,
#             mode="lines+markers",
#             error_x=dict(array=df[unc_col]) if unc_col in df else None,
#             name=name,
#         )
#     )
#     fig.update_yaxes(autorange="reversed", title="Depth (cm)")
#     fig.update_xaxes(title=f"{name} (mBq/g)", type="log" if log_scale else "linear")
#     fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10), title=name)
#     cols[i % n_cols].plotly_chart(fig, width="stretch", key=f"profile_{name}")

# # ------------------------------- Age model ----------------------------------------------#
# if has_age:
#     st.subheader("Age model", divider="gray")

#     fig_age = go.Figure(
#         go.Scatter(x=df["Age"], y=df["Profondeur"], mode="lines+markers", marker=dict(size=8))
#     )
#     fig_age.update_yaxes(autorange="reversed", title="Depth (cm)")
#     fig_age.update_xaxes(title="Age (yr)")
#     fig_age.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
#     st.plotly_chart(fig_age, width="stretch", key="age_chart")

#     if meta.taux_sedimentation:
#         st.caption(f"Constant sedimentation rate: {meta.taux_sedimentation:g} cm/yr.")

# # ------------------------------- Data quality --------------------------------------------#
# st.subheader("Data quality", divider="gray")
# st.caption("Relative uncertainty (1σ) per nuclide — flags low-count measurements.")

# fig_qc = go.Figure()
# for activity_col in activity_cols:
#     name = _nuclide_name(activity_col)
#     unc_col = f"Incertitude {name}"
#     if unc_col not in df:
#         continue
#     relative_uncertainty = (df[unc_col] / df[activity_col]).abs() * 100
#     fig_qc.add_trace(
#         go.Scatter(x=relative_uncertainty, y=depth_mid, mode="lines+markers", name=name)
#     )
# fig_qc.update_yaxes(autorange="reversed", title="Depth (cm)")
# fig_qc.update_xaxes(title="Relative uncertainty (%)")
# fig_qc.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
# st.plotly_chart(fig_qc, width="stretch", key="qc_chart")

# # ------------------------------- Table --------------------------------------------------#
# st.subheader("Table", divider="gray")

# with st.container(border=True):
#     shown = df_view_mode_widget(df, "synthesis", "table")

#     # SERAC is reserved for the synthesis (it's an R age-depth modelling tool).
#     export_dataframe(shown, filename="synthesis", formats=("CSV", "Parquet", "SERAC"))
