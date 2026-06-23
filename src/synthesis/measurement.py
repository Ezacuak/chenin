import math
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Measurement:
    """A value with a 1-sigma uncertainty."""

    value: float
    uncertainty: float

    @property
    def is_nan(self) -> bool:
        """True if the value is missing (NaN)."""
        return math.isnan(self.value)

    @classmethod
    def missing(cls) -> "Measurement":
        """A missing measurement (both fields NaN)."""
        return cls(math.nan, math.nan)

    def __add__(self, other: "Measurement") -> "Measurement":
        return Measurement(
            self.value + other.value,
            _quad(self.uncertainty, other.uncertainty),
        )

    def __sub__(self, other: "Measurement") -> "Measurement":
        return Measurement(
            self.value - other.value,
            _quad(self.uncertainty, other.uncertainty),
        )

    def __mul__(self, other: "Measurement") -> "Measurement":
        value = self.value * other.value
        # relative uncertainties add in quadrature
        rel = _quad(
            _safe_div(self.uncertainty, self.value),
            _safe_div(other.uncertainty, other.value),
        )
        return Measurement(value, abs(value) * rel)

    def __truediv__(self, other: "Measurement") -> "Measurement":
        value = self.value / other.value
        rel = _quad(
            _safe_div(self.uncertainty, self.value),
            _safe_div(other.uncertainty, other.value),
        )
        return Measurement(value, abs(value) * rel)

    def __neg__(self) -> "Measurement":
        return Measurement(-self.value, self.uncertainty)

    @classmethod
    def weighted_mean(cls, measurements: Iterable["Measurement"]) -> "Measurement":
        """Inverse-variance weighted mean of several measurements.

        The scientific standard for combining the activities of a nuclide measured on
        several gamma lines (and what Genie 2000 reports as its weighted mean activity):
        weights are inversely proportional to the variances, and the combined uncertainty
        is ``sqrt(1 / sum(1 / sigma_i^2))``.

        Measurements with a NaN value, a NaN uncertainty, or a non-positive uncertainty
        are skipped. Returns a missing measurement if nothing usable remains.
        """
        weights = 0.0
        weighted_sum = 0.0
        for m in measurements:
            if m.is_nan or math.isnan(m.uncertainty) or m.uncertainty <= 0:
                continue
            w = 1.0 / (m.uncertainty * m.uncertainty)
            weights += w
            weighted_sum += w * m.value

        if weights == 0.0:
            return cls.missing()

        return cls(weighted_sum / weights, math.sqrt(1.0 / weights))


def _quad(a: float, b: float) -> float:
    """Sum two uncertainties in quadrature."""
    return math.sqrt(a * a + b * b)


def _safe_div(a: float, b: float) -> float:
    """Divide, treating division by zero as 0 (no relative contribution)."""
    return a / b if b else 0.0
