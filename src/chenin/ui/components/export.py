import io

import pandas as pd
import streamlit as st

from chenin.serac import export_serac

_DEFAULT_FORMATS = ("CSV", "Parquet")


def _export_widget(df: pd.DataFrame, filename: str, formats: tuple[str, ...]) -> None:
    fmt = st.segmented_control(
        "Export format", list(formats), default=formats[0], key=f"export_fmt_{filename}"
    )

    if fmt == "SERAC":
        # Reserved for the synthesis (SERAC is an R age-depth modelling tool).
        data = export_serac(df)
        mime = "application/octet-stream"
        ext = "serac"
    elif fmt == "Parquet":
        buf = io.BytesIO()
        df.to_parquet(buf, index=False)
        data = buf.getvalue()
        mime = "application/octet-stream"
        ext = "parquet"
    else:  # CSV (default)
        data = df.to_csv(sep=";", index=False, float_format="%.6f").encode("utf-8")
        mime = "text/csv"
        ext = "csv"

    st.download_button(
        label=f"Download ({ext.upper()})",
        data=data,
        file_name=f"{filename}.{ext}",
        mime=mime,
        icon=":material/download:",
    )


def export_dataframe(
    df: pd.DataFrame,
    filename: str = "export",
    formats: tuple[str, ...] = _DEFAULT_FORMATS,
) -> None:
    with st.popover("Export", icon=":material/download:", width="content"):
        _export_widget(df, filename, formats)
