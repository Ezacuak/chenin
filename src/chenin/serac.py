import pandas as pd


def export_serac(df: pd.DataFrame) -> bytes:
    """Export a synthesis dataframe as a SERAC input table (``;``-separated CSV).

    SERAC is an R age-depth modelling tool. It has no place for planned-but-unmeasured
    layers, so rows whose every ``Activite …`` column is empty (the depth-only rows)
    are dropped. When there is nothing nuclide-shaped to filter on, the frame is
    exported as-is.
    """
    activity_cols = [c for c in df.columns if c.startswith("Activite ")]
    if activity_cols:
        has_activity = df[activity_cols].notna().any(axis=1)
        df = df[has_activity]

    csv = df.to_csv(sep=";", index=False, float_format="%.6f")
    return csv.encode("utf-8")
