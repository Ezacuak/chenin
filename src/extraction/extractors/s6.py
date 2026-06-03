import re
import pandas as pd
from ..base import Extractor


class S6Extractor(Extractor):
    def _compile_patterns(self):
        self.s6_header_pattern = re.compile(r"^\s+(.*)$\n^\s+(.*)$", re.MULTILINE)
        self.s6_word_column_pattern = re.compile(r"([A-Za-zÀ-ÿ]+\.?)")
        self.s6_nucleide_line_pattern = re.compile(
            r"^[+>?]\s+([A-Z]{1,2}-\d{1,3})\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)",
            re.MULTILINE,
        )

    def _extract_header(self, content: str) -> list:
        header = []
        lignes = self.s6_header_pattern.findall(content)

        l1 = re.findall(self.s6_word_column_pattern, lignes[0][0])
        l2 = re.findall(self.s6_word_column_pattern, lignes[0][1])

        # Fusion en partant de la fin
        for a, b in zip(reversed(l1), reversed(l2)):
            header.insert(0, f"{a} {b}".strip())

        # Si l1 est plus longue, on conserve le début restant
        if len(l1) > len(l2):
            header = l1[: len(l1) - len(l2)] + header

        return header

    def extract(self, content: str) -> pd.DataFrame:
        header = self._extract_header(content)
        matches = re.findall(self.s6_nucleide_line_pattern, content)

        if not matches:
            return pd.DataFrame()

        df = pd.DataFrame(matches, columns=header)
        df[header[1:]] = df[header[1:]].apply(pd.to_numeric, errors="coerce")

        return df
