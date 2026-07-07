import io

import pandas as pd
import streamlit as st

from serac import export_serac

_DEFAULT_FORMATS = ("CSV", "Parquet")


def _export_widget(df: pd.DataFrame, filename: str, formats: tuple[str, ...]) -> None:
    fmt = st.segmented_control(
        "Format d'export", list(formats), default=formats[0], key=f"export_fmt_{filename}"
    )

    if fmt == "SERAC":
        # Réservé à la synthèse (SERAC est un outil R d'analyse âge-profondeur).
        data = export_serac(df)
        mime = "R/Serac"
        ext = "serac"
    elif fmt == "Parquet":
        buf = io.BytesIO()
        df.to_parquet(buf, index=False)
        data = buf.getvalue()
        mime = "application/octet-stream"
        ext = "parquet"
    else:  # CSV (défaut)
        data = df.to_csv(sep=";", index=False, float_format="%.6f").encode("utf-8")
        mime = "text/csv"
        ext = "csv"

    st.download_button(
        label=f"Télécharger ({ext.upper()})",
        data=data,
        file_name=f"{filename}.{ext}",
        mime=mime,
    )


def export_dataframe(
    df: pd.DataFrame,
    filename: str = "export",
    formats: tuple[str, ...] = _DEFAULT_FORMATS,
) -> None:
    with st.popover("Exporter", icon=":material/download:", width="content"):
        _export_widget(df, filename, formats)
