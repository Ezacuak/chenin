import plotly.graph_objects as go
import state
import streamlit as st
from components.export import export_dataframe
from streamlit_extras.dataframe_explorer import dataframe_explorer
from streamlit_pivot import st_pivot_table

from g2k_parser import format_nuclide
from synthesis import SynthesisBuilder

st.title("Synthèse")
st.markdown("Construire une synthèse à partir du fichier build chargé.")

config = state.get_build_config()
reports = state.get_reports()

if config is None or not reports:
    st.info(
        "Importez un fichier build (.toml) dans la barre latérale pour construire la synthèse."
    )
    st.stop()

# ----------------------------- Aperçu de la configuration ---------------------------#
with st.expander(f"Configuration : {config.title}", expanded=False):
    st.markdown(
        f"**Metadata:** :green-badge[Année: {config.metadata.base_year}] "
        f":green-badge[Taux de sedimentation: {config.metadata.taux_sedimentation}]"
    )

    st.markdown("**Nuclides:**")
    for key, nuclide in config.nuclides.items():
        peaks = ", ".join(
            f"`{format_nuclide(p.nuclide)}` @ {p.energy} keV" for p in nuclide.peaks
        )
        st.markdown(peaks)

    st.markdown("**Colonnes:**")
    for column in config.columns:
        source = (
            f"source={column.source}"
            if column.source is not None
            else f"formule={column.formula}"
        )
        st.markdown(f"`{column.name}`: {source}")

# ----------------------------- Construction de la synthèse --------------------------#
try:
    df = SynthesisBuilder(config).build(reports)
except Exception as e:
    st.error(f"Erreur lors de la génération : {e}")
    st.stop()

state.store_synthesis(df)

activity_cols = [c for c in df.columns if c.startswith("Activite ")]
depth_top = df["Profondeur"]
depth_bot = df["Profondeur"] + df["Epaisseur"]
depth_mid = df["Profondeur"] + df["Epaisseur"] / 2


def _nuclide_name(activity_col: str) -> str:
    return activity_col.removeprefix("Activite ")


# ------------------------------- Vue « carotte » ------------------------------------#
st.subheader("Carotte", divider="gray")

color_col = st.selectbox(
    "Colorer les couches par",
    activity_cols,
    format_func=_nuclide_name,
    key="core_color",
)

core_col, legend_col = st.columns([1, 3])

with core_col:
    fig_core = go.Figure(
        go.Bar(
            x=["Carotte"] * len(df),
            y=df["Epaisseur"],
            base=depth_top,
            marker=dict(
                color=df[color_col],
                colorscale="Viridis",
                colorbar=dict(title=_nuclide_name(color_col)),
                line=dict(color="rgba(0,0,0,0.3)", width=1),
            ),
            customdata=list(zip(depth_top, depth_bot, df[color_col])),
            hovertemplate=(
                "Couche %{customdata[0]:.1f}–%{customdata[1]:.1f} cm<br>"
                f"{_nuclide_name(color_col)}: %{{customdata[2]:.1f}} mBq/g<extra></extra>"
            ),
        )
    )
    fig_core.update_yaxes(autorange="reversed", title="Profondeur (cm)")
    fig_core.update_xaxes(showticklabels=False)
    fig_core.update_layout(height=520, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_core, width="stretch", key="core_chart")

with legend_col:
    st.caption(
        "Chaque bande est un échantillon, du sommet (`depth_top`) au fond (`depth_bot`). "
        "La couleur encode l'activité choisie."
    )
    st.dataframe(
        df[["Profondeur", "Epaisseur", color_col, "Age"]].rename(
            columns={color_col: _nuclide_name(color_col)}
        ),
        hide_index=True,
        width="stretch",
    )

# ------------------------------- Profils de profondeur ------------------------------#
st.subheader("Profils", divider="gray")

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
    fig.update_yaxes(autorange="reversed", title="Profondeur (cm)")
    fig.update_xaxes(title=f"{name} (mBq/g)")
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10), title=name)
    cols[i % n_cols].plotly_chart(fig, width="stretch", key=f"profile_{name}")

# ------------------------------- Tableau de synthèse --------------------------------#
st.subheader("Tableau", divider="gray")

with st.container(border=True):
    _TABLE, _PIVOT, _FILTERED = "Tableau", "Pivot", "Filtre"

    with st.container(
        horizontal=True,
        horizontal_alignment="distribute",
        vertical_alignment="center",
    ):
        st.caption(
            f":material/table_rows: {len(df)} lignes "
            f"· :material/view_column: {len(df.columns)} colonnes"
        )
        view = st.segmented_control(
            "Affichage",
            [_TABLE, _PIVOT, _FILTERED],
            default=_TABLE,
            key="view_synthesis",
            label_visibility="collapsed",
            width="content",
        )

    if view == _PIVOT:
        st_pivot_table(df, key="pivot_synthesis")
    elif view == _FILTERED:
        st.dataframe(dataframe_explorer(df))
    else:
        st.dataframe(df, hide_index=True)

    # SERAC réservé à la synthèse (outil R d'analyse âge-profondeur).
    export_dataframe(df, filename="synthesis", formats=("CSV", "Parquet", "SERAC"))
