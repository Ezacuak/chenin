import ast

import pandas as pd

from g2k_parser import columns as C

from .config import NuclideSpec
from .measurement import Measurement

# Section-3 column names — single source of truth in g2k_parser.columns.
NUCLIDE_COL = C.NUCLEIDE
ENERGY_COL = C.ENERGIE_KEV
ACTIVITY_COL = C.ACTIVITE_MBQ
UNCERTAINTY_COL = C.INCERT_MBQ

# Tolerance (keV) when matching a configured peak energy to a section-3 row.
ENERGY_TOLERANCE = 1.0


def _numeric_rows(s3, nuclide: str):
    """Rows of section 3 for a nuclide, with energy/activity/uncertainty as floats."""
    rows = s3[s3[NUCLIDE_COL] == nuclide]
    if rows.empty:
        return rows
    return rows.assign(
        **{
            ENERGY_COL: pd.to_numeric(rows[ENERGY_COL], errors="coerce"),
            ACTIVITY_COL: pd.to_numeric(rows[ACTIVITY_COL], errors="coerce"),
            UNCERTAINTY_COL: pd.to_numeric(rows[UNCERTAINTY_COL], errors="coerce"),
        }
    )


def _peak_measurement(s3, nuclide: str, energy: float) -> Measurement:
    """Activity of one (nuclide, energy) peak from section 3, nearest within tolerance."""
    rows = _numeric_rows(s3, nuclide)
    if rows.empty:
        return Measurement.missing()

    deltas = (rows[ENERGY_COL] - energy).abs()
    nearest = deltas.idxmin()
    if not (deltas[nearest] <= ENERGY_TOLERANCE):  # also handles NaN delta
        return Measurement.missing()

    activity = rows.loc[nearest, ACTIVITY_COL]
    if pd.isna(activity):
        return Measurement.missing()

    return Measurement(
        float(activity),
        float(rows.loc[nearest, UNCERTAINTY_COL]),
    )


def resolve_nuclide(s3, spec: NuclideSpec) -> Measurement:
    """Inverse-variance weighted mean over a nuclide's configured peaks."""
    measurements = [
        _peak_measurement(s3, peak.nuclide, peak.energy) for peak in spec.peaks
    ]
    return Measurement.weighted_mean(measurements)


# --- safe formula evaluation -------------------------------------------------

_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div)


def evaluate_formula(formula: str, namespace: dict[str, Measurement]) -> Measurement:
    """Evaluate an arithmetic formula over resolved nuclide measurements.

    Names refer to nuclide keys (valid identifiers); only names, numeric constants and
    ``+ - * /`` (binary and unary) are permitted.
    """
    tree = ast.parse(formula, mode="eval")
    return _eval_node(tree.body, namespace)


def _eval_node(node, namespace: dict[str, Measurement]) -> Measurement:
    if isinstance(node, ast.BinOp):
        if not isinstance(node.op, _ALLOWED_BINOPS):
            raise ValueError(f"operator {type(node.op).__name__} is not allowed")
        left = _eval_node(node.left, namespace)
        right = _eval_node(node.right, namespace)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        return left / right

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        operand = _eval_node(node.operand, namespace)
        return -operand if isinstance(node.op, ast.USub) else operand

    if isinstance(node, ast.Name):
        if node.id not in namespace:
            raise ValueError(f"unknown nuclide '{node.id}' in formula")
        return namespace[node.id]

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Measurement(float(node.value), 0.0)

    raise ValueError(f"unsupported expression element: {type(node).__name__}")
