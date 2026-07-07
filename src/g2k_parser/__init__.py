from . import columns
from .parser import G2KParser
from .report import Report
from .utils import format_nuclide

SECTION_DESCRIPTIONS = {
    "s1": "Rapport de l'analyse du spectre (métadonnées)",
    "s2": "Rapport analyse des pics",
    "s3": "Rapport identification des nucléides",
    "s4_nucleides": "Rapport identification avec correction d'interférence — nucléides",
    "s4_pics": "Rapport identification avec correction d'interférence — pics",
    "s5": "Rapport limites de détection",
    "s6": "Rapport limites de détection ISO 11929",
}

__all__ = ["G2KParser", "Report", "SECTION_DESCRIPTIONS", "columns", "format_nuclide"]
