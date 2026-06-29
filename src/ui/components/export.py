import io

import pandas as pd
import streamlit as st

from serac import export_serac

_FORMATS = ["CSV", "Parquet", "SERAC"]


def _export_widget(df: pd.DataFrame, filename: str = "export") -> None:
    fmt = st.segmented_control(
        "Format d'export", _FORMATS, default="CSV", key=f"export_fmt_{filename}"
    )

    if fmt == "CSV":
        data = df.to_csv(sep=";", index=False, float_format="%.6f").encode("utf-8")
        mime = "text/csv"
        ext = "csv"
    elif fmt == "SERAC":
        data = export_serac(df)
        mime = "R/Serac"
        ext = "serac"
    else:
        buf = io.BytesIO()
        df.to_parquet(buf, index=False)
        data = buf.getvalue()
        mime = "application/octet-stream"
        ext = "parquet"

    st.download_button(
        label=f"Télécharger ({ext.upper()})",
        data=data,
        file_name=f"{filename}.{ext}",
        mime=mime,
    )


def export_dataframe(df: pd.DataFrame, filename: str = "export") -> None:
    with st.popover("Exporter", icon=":material/download:", width="content"):
        _export_widget(df, filename)
