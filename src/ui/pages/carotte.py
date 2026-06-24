import plotly.graph_objects as go
import streamlit as st

import state
from g2k_parser import SECTION_DESCRIPTIONS

st.title("Visualisation de la carotte")

df, order = state.get_synthesis()
if df is None:
    st.info("Générez d'abord une synthèse dans l'onglet « Constructeur de synthèse ».")
    st.stop()

activity_cols = [c for c in df.columns if c.startswith("Activite ")]
if not activity_cols:
    st.warning("La synthèse ne contient aucune colonne d'activité à afficher.")
    st.stop()

color_col = st.selectbox(
    "Colorer les tranches par",
    options=activity_cols,
    format_func=lambda c: c.removeprefix("Activite "),
)

# Each sample is a slice spanning [Profondeur, Profondeur + Epaisseur].
customdata = df[
    ["Numero Echantillon", "Profondeur", "Epaisseur", "Age", color_col]
].to_numpy()

fig = go.Figure(
    go.Bar(
        x=["Carotte"] * len(df),
        y=df["Epaisseur"],
        base=df["Profondeur"],
        marker=dict(
            color=df[color_col],
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title=color_col.removeprefix("Activite ")),
            line=dict(color="rgba(0,0,0,0.3)", width=1),
        ),
        customdata=customdata,
        hovertemplate=(
            "Échantillon %{customdata[0]}<br>"
            "Profondeur %{customdata[1]:.2f} cm<br>"
            "Épaisseur %{customdata[2]:.2f} cm<br>"
            "Âge %{customdata[3]:.1f}<br>"
            "Activité %{customdata[4]:.3g}<extra></extra>"
        ),
    )
)
fig.update_layout(
    barmode="overlay",
    yaxis=dict(title="Profondeur (cm)", autorange="reversed"),
    xaxis=dict(showticklabels=False),
    height=600,
    margin=dict(l=10, r=10, t=10, b=10),
)

event = st.plotly_chart(
    fig,
    use_container_width=True,
    on_select="rerun",
    selection_mode="points",
)

points = event.get("selection", {}).get("points", []) if event else []
if not points:
    st.info("Survolez une tranche pour les infos, cliquez pour le détail du rapport.")
    st.stop()

selected_numero = points[0]["customdata"][0]
row = df[df["Numero Echantillon"] == selected_numero]
if row.empty:
    st.stop()

st.subheader(f"Échantillon {selected_numero}")
st.dataframe(row, use_container_width=True, hide_index=True)

report_name = order.get(selected_numero)
reports, _ = state.get_reports()
report = reports.get(report_name) if report_name else None

if report is None:
    st.caption("Rapport G2K source introuvable en session.")
    st.stop()

with st.expander(f"Rapport G2K complet — {report_name}"):
    for key in report:
        st.markdown(f"**{SECTION_DESCRIPTIONS[key]}**")
        st.dataframe(report[key], use_container_width=True)
