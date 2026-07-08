from pathlib import Path
from typing import IO

import pandas as pd

from chenin.g2k_parser import Report

from .config import BuildConfig, SampleSpec
from .measurement import Measurement
from .providers import evaluate_formula, resolve_nuclide


class SynthesisBuilder:
    """Build a synthesis ``DataFrame`` from reports using a build configuration."""

    def __init__(self, config: BuildConfig):
        self.config = config

    @classmethod
    def from_toml(cls, file: str | Path | IO[bytes]) -> SynthesisBuilder:
        """Create a builder from a TOML build file."""
        return cls(BuildConfig.from_toml(file))

    def build(self, reports: dict[str, Report]) -> pd.DataFrame:
        """Build the synthesis: one row per sample, in build-file order.

        ``reports`` maps a sample ``name`` to its parsed Report (see ``load_reports``).
        """
        rows = []
        for sample in self.config.samples:
            report = reports.get(sample.name)
            if report is None:
                raise KeyError(f"no report loaded for sample '{sample.name}'")
            rows.append(self._build_row(sample, report))
        return pd.DataFrame(rows)

    def _has_age_model(self) -> bool:
        meta = self.config.metadata
        return meta.base_year is not None and bool(meta.taux_sedimentation)

    def _build_row(self, sample: SampleSpec, report: Report) -> dict:
        section = report["s3"]
        meta = self.config.metadata

        row: dict = {
            "Profondeur": sample.depth_top,
            "Epaisseur": sample.depth_bot - sample.depth_top,
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

        # Age from a constant sedimentation rate — only when the model is configured.
        if self._has_age_model():
            row["Age"] = meta.base_year - sample.depth_top / meta.taux_sedimentation

        return row
