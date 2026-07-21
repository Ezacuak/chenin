"""SERAC export: format a synthesis DataFrame as a serac (R package) input file.

serac (age-depth modelling, https://github.com/EDYTEM/serac — see
``serac_input_formatting()``) expects a tab-separated table with depths in mm:
``depth_top``, ``depth_bottom``, ``density``, ``Pbex``, ``Pbex_er``, ``Cs``,
``Cs_er``, ``Am``, ``Am_er``. The synthesis DataFrame built by
``SynthesisBuilder`` uses cm and French column names driven by the synthesis
template (``Activite <name>``/``Incertitude <name>``), so this module converts
depth units and renames columns rather than assuming a fixed template.
"""

import pandas as pd

SERAC_COLUMNS = [
    "depth_top",
    "depth_bottom",
    "density",
    "Pbex",
    "Pbex_er",
    "Cs",
    "Cs_er",
    "Am",
    "Am_er",
]

# serac column -> packaged default template's display name for that nuclide.
# Override via `nuclide_columns` for a custom template using different names.
DEFAULT_NUCLIDE_COLUMNS = {
    "Pbex": "PB-Exc",
    "Cs": "CS-137",
    "Am": "AM-241",
}


def export_serac(
    df: pd.DataFrame,
    *,
    nuclide_columns: dict[str, str] | None = None,
    depth_cm_to_mm: bool = True,
) -> bytes:
    """Format a synthesis DataFrame as a serac input file (tab-separated, mm depths).

    ``nuclide_columns`` maps a serac name (``Pbex``, ``Cs``, ``Am``, ...) to the
    synthesis template's display name for that nuclide; defaults to the packaged
    lab template (``PB-Exc``, ``CS-137``, ``AM-241``). ``depth_cm_to_mm`` converts
    the synthesis's cm depths to the mm serac expects; set to ``False`` if ``df``
    is already in mm.
    """
    nuclide_columns = {**DEFAULT_NUCLIDE_COLUMNS, **(nuclide_columns or {})}
    factor = 10.0 if depth_cm_to_mm else 1.0

    out = pd.DataFrame(
        {
            "depth_top": df["Profondeur"] * factor,
            "depth_bottom": (df["Profondeur"] + df["Epaisseur"]) * factor,
            "density": df["DBD"],
        }
    )

    for serac_name, synthesis_name in nuclide_columns.items():
        activity_col = f"Activite {synthesis_name}"
        uncertainty_col = f"Incertitude {synthesis_name}"
        if activity_col not in df.columns or uncertainty_col not in df.columns:
            raise ValueError(
                f"synthesis has no '{activity_col}'/'{uncertainty_col}' column for "
                f"'{serac_name}' (available: {list(df.columns)})"
            )
        out[serac_name] = df[activity_col]
        out[f"{serac_name}_er"] = df[uncertainty_col]

    out = out[[c for c in SERAC_COLUMNS if c in out.columns]]
    return out.to_csv(sep="\t", index=False, float_format="%.6f").encode("utf-8")
