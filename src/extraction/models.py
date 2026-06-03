from dataclasses import dataclass
from typing import Optional


@dataclass
class PeakData:
    peak_number: int
    start_channel: float
    end_channel: float
    centroid: float
    energy_kev: float
    fwhm_kev: float
    surface: float
    uncertainty: float
    background: float


@dataclass
class NuclideLimitData:
    nucleide_name: str
    marker: str
    values: dict
