from collections.abc import Mapping
from typing import Any

from g2k_parser import G2KParser, Parser


class Report(Mapping):
    def __init__(self, path: str, parser: Parser | None = None) -> None:
        self.filepath = path
        self.parser = parser or G2KParser()
        self._data = self.parser.parse(path)

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, int):
            return list(self._data.values())[key]
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __str__(self) -> str:
        return "\n".join(str(df) for df in self._data.values())
