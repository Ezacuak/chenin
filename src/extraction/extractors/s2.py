import re
import pandas as pd
from ..base import Extractor


class S2Extractor(Extractor):
    COLUMNS = [
        "Numéro du pic",
        "Début (canaux)",
        "Fin (canaux)",
        "Centroïde",
        "Energie (keV)",
        "FWHM (keV)",
        "Surface",
        "Incert.",
        "Fond sous le pic",
    ]

    def _compile_patterns(self):
        self.data_pattern = re.compile(
            r"^\s*[MmF]?\s*(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+"
            r"(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+-\s*"
            r"(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+"
            r"(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+"
            r"(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+"
            r"(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+"
            r"(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+"
            r"(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+"
            r"(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)",
            re.MULTILINE,
        )
        self.footer_pattern = re.compile(r"^Page\s+\d+\s+sur\s+\d+$", re.MULTILINE)

    def extract(self, content: str) -> pd.DataFrame:
        cleaned_content = self._remove_footers(content)
        matches = self.data_pattern.findall(cleaned_content)

        df = pd.DataFrame(matches, columns=self.COLUMNS)
        df[self.COLUMNS] = df[self.COLUMNS].apply(pd.to_numeric, errors="coerce")

        return df

    def _remove_footers(self, content: str) -> str:
        footers = list(self.footer_pattern.finditer(content))
        for i, f in enumerate(footers):
            start = f.start()
            end = footers[i + 1].start() if i + 1 < len(footers) else len(content)
            content = content[:start] + content[end:]
        return content
