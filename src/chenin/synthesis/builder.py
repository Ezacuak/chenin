from pathlib import Path
from typing import IO

import numpy as np
import pandas as pd

from chenin.g2k_parser import Report

from .config import BuildConfig, ColumnSpec, SampleSpec
from .measurement import Measurement
from .providers import evaluate_formula, resolve_nuclide


class SynthesisBuilder:
    """Build a synthesis ``DataFrame`` from reports using a build configuration."""

    def __init__(self, config: BuildConfig):
        self.config = config

    @classmethod
    def from_template(
        cls,
        template: str | Path | IO | None,
        samples: list[SampleSpec],
        **kwargs,
    ) -> SynthesisBuilder:
        """Create a builder from a synthesis template and a sample list."""
        return cls(BuildConfig.from_template(template, samples, **kwargs))

    def build(self, reports: dict[str, Report]) -> pd.DataFrame:
        """Build the synthesis: one row per sample, ordered by depth.

        ``reports`` maps a report key to its parsed Report (see ``load_reports``).
        Samples with no matching report become depth-only rows (activities are NaN).
        """
        ordered = sorted(self.config.samples, key=lambda s: s.depth_top)
        rows = [self._build_row(sample, reports.get(sample.report)) for sample in ordered]
        return pd.DataFrame(rows)

    def _build_row(self, sample: SampleSpec, report: Report | None) -> dict:
        # Resolve every nuclide source once; measured columns then read a source and
        # derived ones evaluate a formula over the same namespace.
        nuclides: dict[str, Measurement] = {}
        if report is not None:
            section = report["s3"]
            nuclides = {
                key: resolve_nuclide(section, spec) for key, spec in self.config.nuclides.items()
            }

        row: dict = {}
        for col in self.config.columns:
            if col.is_geometry:
                value = getattr(sample, col.geometry)
                # None would make the whole column object-dtype; only the sample code
                # is genuinely textual.
                if value is None and col.geometry != "sample_code":
                    value = np.nan
                row[col.name] = value
            elif report is None:
                # Depth-only row: keep the geometry, leave every activity blank.
                row[f"Activite {col.name}"] = np.nan
                row[f"Incertitude {col.name}"] = np.nan
            else:
                m = self._measure(col, nuclides)
                row[f"Activite {col.name}"] = m.value
                row[f"Incertitude {col.name}"] = m.uncertainty

        return row

    @staticmethod
    def _measure(col: ColumnSpec, nuclides: dict[str, Measurement]) -> Measurement:
        if col.source is not None:
            return nuclides[col.source]
        return evaluate_formula(col.formula, nuclides)
