import re
import pandas as pd
from pathlib import Path
from .extractors.s2 import S2Extractor
from .extractors.s6 import S6Extractor


class Report:
    def __init__(self, path: str, content: str):
        self.path = Path(path)
        self.content = content
        self.sections = {}
        self._split_sections()
        self.s2_extractor = S2Extractor()
        self.s6_extractor = S6Extractor()

    @classmethod
    def from_file(cls, path: str) -> "Report":
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return cls(path, content)

    def _split_sections(self):
        section_pattern = re.compile(
            r"^\*+$\n^\*{5}(.*)\*{5}$\n^\*+$", re.MULTILINE
        )
        headers = section_pattern.findall(self.content)
        matches = list(section_pattern.finditer(self.content))

        for i, match in enumerate(matches):
            title = match.group(1).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(self.content)
            self.sections[title] = self.content[start:end].strip()

    def extract_s2(self) -> pd.DataFrame:
        s2_title = self._find_section_title("RAPPORT ANALYSE DES PICS")
        if not s2_title or s2_title not in self.sections:
            return pd.DataFrame()
        return self.s2_extractor.extract(self.sections[s2_title])

    def extract_s6(self) -> pd.DataFrame:
        s6_title = self._find_section_title("ISO 11929")
        if not s6_title or s6_title not in self.sections:
            return pd.DataFrame()
        return self.s6_extractor.extract(self.sections[s6_title])

    def _find_section_title(self, search_term: str) -> str:
        for title in self.sections.keys():
            if search_term in title:
                return title
        return None
