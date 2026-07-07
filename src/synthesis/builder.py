import math
import re
from io import BufferedReader

import pandas as pd

from g2k_parser import Report

from .config import SynthesisConfig
from .measurement import Measurement
from .providers import evaluate_formula, resolve_nuclide

_NUMERO_RE = re.compile(r"(\d+)(?!.*\d)")  # last integer in a string


class SynthesisBuilder:
    """Build a synthesis ``DataFrame`` from reports using a configuration."""

    def __init__(self, config: SynthesisConfig):
        self.config = config

    @classmethod
    def from_toml(cls, file: str | BufferedReader) -> "SynthesisBuilder":
        """Create a builder from a TOML configuration file."""
        return cls(SynthesisConfig.from_toml(file))

    def build(self, reports: list[Report]) -> pd.DataFrame:
        """Build the synthesis: one row per report, in the given order."""
        rows = []
        depth = 0.0
        for report in reports:
            row, depth = self._build_row(report, depth)
            rows.append(row)
        return pd.DataFrame(rows)

    def _build_row(self, report: Report, depth: float) -> tuple[dict, float]:
        section = report["s3"]
        meta = self.config.metadata
        epaisseur = meta.epaisseur

        row: dict = {
            "Profondeur": depth,
            "Epaisseur": epaisseur,
        }

        # Resolve every nuclide source once; columns then read a source or a formula.
        nuclides: dict[str, Measurement] = {
            key: resolve_nuclide(section, spec)
            for key, spec in self.config.nuclides.items()
        }

        for col in self.config.columns:
            if col.source is not None:
                m = nuclides[col.source]
            else:
                m = evaluate_formula(col.formula, nuclides)
            row[f"Activite {col.name}"] = m.value
            row[f"Incertitude {col.name}"] = m.uncertainty

        row["Age"] = _age(depth, meta.base_year, meta.taux_sedimentation)

        next_depth = depth + epaisseur if epaisseur is not None else depth
        return row, next_depth


def _age(depth: float, base_year, taux_sedimentation) -> float:
    """Age = base_year - depth / taux_sedimentation (NaN if inputs are missing)."""
    if base_year is None or not taux_sedimentation:
        return math.nan
    return base_year - depth / taux_sedimentation
