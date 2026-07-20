from . import columns
from .parser import G2KParser
from .report import Report
from .utils import format_nuclide

SECTION_DESCRIPTIONS = {
    "s1": "Spectrum analysis report (metadata)",
    "s2": "Peak analysis report",
    "s3": "Nuclide identification report",
    "s4_nucleides": "Interference-corrected identification — nuclides",
    "s4_pics": "Interference-corrected identification — peaks",
    "s5": "Detection limits report",
    "s6": "Detection limits report (ISO 11929)",
}

__all__ = ["G2KParser", "Report", "SECTION_DESCRIPTIONS", "columns", "format_nuclide"]
