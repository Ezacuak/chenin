import ast
import re

import pandas as pd

from g2k_parser import columns as C

from .config import ColumnSpec, Peak
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


def _nuclide_measurements(s3, nuclide: str) -> list[Measurement]:
    """All usable peak measurements of a nuclide from section 3."""
    rows = _numeric_rows(s3, nuclide)
    measurements = []
    for _, row in rows.iterrows():
        activity = row[ACTIVITY_COL]
        if pd.isna(activity):
            continue
        measurements.append(Measurement(float(activity), float(row[UNCERTAINTY_COL])))
    return measurements


class ReportProvider:
    """Resolve a nuclide's activity directly from section 3."""

    def __init__(self, spec: ColumnSpec):
        self.name = spec.name
        self.energy = spec.energy

    def resolve(self, s3, _resolved: dict[str, Measurement]) -> Measurement:
        if self.energy is not None:
            return _peak_measurement(s3, self.name, self.energy)
        return Measurement.weighted_mean(_nuclide_measurements(s3, self.name))


class MeanProvider:
    """Inverse-variance weighted mean over an explicit set of peaks."""

    def __init__(self, spec: ColumnSpec):
        self.peaks: list[Peak] = spec.peaks

    def resolve(self, s3, _resolved: dict[str, Measurement]) -> Measurement:
        measurements = [
            _peak_measurement(s3, peak.nuclide, peak.energy) for peak in self.peaks
        ]
        return Measurement.weighted_mean(measurements)


class CalculatedProvider:
    """Evaluate a formula over already-resolved element measurements."""

    def __init__(self, spec: ColumnSpec):
        self.formula = spec.formula

    def resolve(self, _s3, resolved: dict[str, Measurement]) -> Measurement:
        return _safe_eval(self.formula, resolved)


def build_provider(spec: ColumnSpec):
    """Factory: pick the provider strategy for a column spec."""
    if spec.provider == "report":
        return ReportProvider(spec)
    if spec.provider == "mean":
        return MeanProvider(spec)
    if spec.provider == "calculated":
        return CalculatedProvider(spec)
    raise ValueError(f"unknown provider '{spec.provider}'")


# --- safe formula evaluation -------------------------------------------------

# Element names like "PB-210" or "PB-Exc" are not valid Python identifiers; map them to
# sanitized identifiers before parsing, and look those up in the namespace.
_NAME_RE = re.compile(r"[A-Za-z]{1,2}-[A-Za-z0-9]{1,4}")

_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div)


def _sanitize(name: str) -> str:
    return name.replace("-", "_")


def _safe_eval(formula: str, resolved: dict[str, Measurement]) -> Measurement:
    """Evaluate an arithmetic formula over resolved element measurements.

    Only names, numeric constants and ``+ - * /`` (binary and unary) are permitted.
    """
    namespace = {_sanitize(name): m for name, m in resolved.items()}
    expr = _NAME_RE.sub(lambda m: _sanitize(m.group(0)), formula)

    tree = ast.parse(expr, mode="eval")
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
            raise ValueError(f"unknown element '{node.id}' in formula")
        return namespace[node.id]

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Measurement(float(node.value), 0.0)

    raise ValueError(f"unsupported expression element: {type(node).__name__}")
