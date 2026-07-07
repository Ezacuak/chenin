from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .parser import G2KParser


class Report(Mapping):
    """
    Build report from a parser

    For now just G2K

    What is that ?

    It's a list of 6 section.
    Each section is Dataframe (Pandas)
    """

    def __init__(
        self, local_path: str, temp_path: str, parser: G2KParser | None = None
    ) -> None:
        self.local_path = local_path
        self.temp_path = temp_path
        self.name = Path(local_path).stem
        self.parser = parser or G2KParser()
        self._data = self.parser.parse(temp_path)

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
