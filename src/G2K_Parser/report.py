from collections.abc import Mapping
from typing import Any, Dict

from ._sections import (
    extract_data_1_s4,
    extract_data_2_s4,
    extract_data_s2,
    extract_data_s3,
    extract_data_s5,
    extract_data_s6,
    extract_header_1_s4,
    extract_header_2_s4,
    extract_header_s2,
    extract_header_s3,
    extract_header_s5,
    extract_header_s6,
    extract_s1,
)
from .utils import Utils


class Report(Mapping):
    def __init__(self, path: str) -> None:
        self.file = path
        self.report = self._parse_report()
        self._parse_report()

    def _parse_report(self) -> Dict:
        with open(self.file) as f:
            content = f.read()

        titles, sections = Utils.split_sections(content)

        data_s1 = extract_s1(sections[titles[0]])

        header_s2 = extract_header_s2(sections[titles[1]])
        data_s2 = extract_data_s2(sections[titles[1]], header_s2)

        header_s3 = extract_header_s3(sections[titles[2]])
        data_s3 = extract_data_s3(sections[titles[2]], header_s3)

        header_1_s4 = extract_header_1_s4(sections[titles[3]])
        header_2_s4 = extract_header_2_s4(sections[titles[3]])
        data_1_s4 = extract_data_1_s4(sections[titles[3]], header_1_s4)
        data_2_s4 = extract_data_2_s4(sections[titles[3]], header_2_s4)

        header_s5 = extract_header_s5(sections[titles[4]])
        data_s5 = extract_data_s5(sections[titles[4]], header_s5)

        header_s6 = extract_header_s6(sections[titles[5]])
        data_s6 = extract_data_s6(sections[titles[5]], header_s6)

        return {
            "s1": Utils.normalize_columns(data_s1),
            "s2": Utils.normalize_columns(data_s2),
            "s3": Utils.normalize_columns(data_s3),
            "s4_nucleides": Utils.normalize_columns(data_1_s4),
            "s4_pics": Utils.normalize_columns(data_2_s4),
            "s5": Utils.normalize_columns(data_s5),
            "s6": Utils.normalize_columns(data_s6),
        }

    def to_csv(self):
        for df in self.report:
            pass

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, int):
            return list(self.report.values())[key]
        return self.report[key]

    def __iter__(self):
        return iter(self.report)

    def __len__(self) -> int:
        return len(self.report)

    def __str__(self) -> str:
        sb = ""

        for k, v in self.report.items():
            sb += f"{v}\n"

        return sb
