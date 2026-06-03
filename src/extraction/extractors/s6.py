import re
import pandas as pd
from ..base import Extractor


class S6Extractor(Extractor):
    def _compile_patterns(self):
        self.marker_pattern = re.compile(
            r"^([+>?])\s+([A-Z]{1,2}-\d{1,3})\s+(.*)$", re.MULTILINE
        )

    def extract(self, content: str) -> pd.DataFrame:
        matches = self.marker_pattern.findall(content)

        if not matches:
            return pd.DataFrame()

        data = []
        num_values = None

        for marker, nucleide, rest_values in matches:
            values = rest_values.split()
            if num_values is None:
                num_values = len(values)
            data.append([marker, nucleide] + values[:num_values])

        header = ["Marker", "Nucleide"] + [f"Value_{i+1}" for i in range(num_values)]
        df = pd.DataFrame(data, columns=header)

        numeric_cols = header[2:]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

        return df
