from pathlib import Path
from typing import IO

import numpy as np
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
    def from_roadmap(
        cls,
        roadmap: str | Path | IO,
        template: str | Path | IO | None = None,
    ) -> SynthesisBuilder:
        """Create a builder from a roadmap file and an optional synthesis template."""
        return cls(BuildConfig.from_roadmap(roadmap, template))

    def build(self, reports: dict[str, Report]) -> pd.DataFrame:
        """Build the synthesis: one row per sample, in roadmap order.

        ``reports`` maps a sample ``name`` to its parsed Report (see ``load_reports``).
        Samples with no loaded report become depth-only rows (activities are NaN).
        """
        rows = [self._build_row(sample, reports.get(sample.name)) for sample in self.config.samples]
        return pd.DataFrame(rows)

    def _has_age_model(self) -> bool:
        meta = self.config.metadata
        return meta.base_year is not None and bool(meta.taux_sedimentation)

    def _build_row(self, sample: SampleSpec, report: Report | None) -> dict:
        meta = self.config.metadata

        row: dict = {
            "Echantillon": sample.sample_code,
            "Profondeur": sample.depth_top,
            "Epaisseur": sample.depth_bot - sample.depth_top,
            "DBD": sample.dbd,
        }

        if report is None:
            # Depth-only row: keep the geometry, leave every activity blank.
            for col in self.config.columns:
                row[f"Activite {col.name}"] = np.nan
                row[f"Incertitude {col.name}"] = np.nan
        else:
            section = report["s3"]
            # Resolve every nuclide source once; columns read a source or a formula.
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
