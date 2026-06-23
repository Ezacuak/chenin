import math
import re

import pandas as pd

from report import Report

from .config import SynthesisConfig
from .measurement import Measurement
from .providers import build_provider

_NUMERO_RE = re.compile(r"(\d+)(?!.*\d)")  # last integer in a string


class SynthesisBuilder:
    """Build a synthesis ``DataFrame`` from reports using a configuration."""

    def __init__(self, config: SynthesisConfig):
        self.config = config
        self._providers = {col.key: build_provider(col) for col in config.columns}

    @classmethod
    def from_toml(cls, path: str) -> "SynthesisBuilder":
        """Create a builder from a TOML configuration file."""
        return cls(SynthesisConfig.from_toml(path))

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
            "Numero Echantillon": _numero(report),
            "Profondeur": depth,
            "Epaisseur": epaisseur,
        }

        # Resolve report/mean columns first, then calculated ones (which depend on them).
        resolved: dict[str, Measurement] = {}
        for col in self.config.columns:
            if col.provider != "calculated":
                resolved[col.name] = self._providers[col.key].resolve(section, resolved)
        for col in self.config.columns:
            if col.provider == "calculated":
                resolved[col.name] = self._providers[col.key].resolve(section, resolved)

        for col in self.config.columns:
            m = resolved[col.name]
            row[f"Activite {col.name}"] = m.value
            row[f"Incertitude {col.name}"] = m.uncertainty

        row["Age"] = _age(depth, meta.base_year, meta.taux_sedimentation)

        next_depth = depth + epaisseur if epaisseur is not None else depth
        return row, next_depth


def _numero(report: Report):
    """Sample number from the report filename (last integer), else the filename stem."""
    stem = report.filepath.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    match = _NUMERO_RE.search(stem)
    return int(match.group(1)) if match else stem


def _age(depth: float, base_year, taux_sedimentation) -> float:
    """Age = base_year - depth / taux_sedimentation (NaN if inputs are missing)."""
    if base_year is None or not taux_sedimentation:
        return math.nan
    return base_year - depth / taux_sedimentation
