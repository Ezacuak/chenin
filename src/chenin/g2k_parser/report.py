from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .parser import G2KParser


class Report(Mapping):
    """A parsed Génie 2000 report: an ordered, read-only mapping of sections.

    Each section (``s1``–``s6``) is a :class:`pandas.DataFrame`. Sections are
    reachable both by string key (``report["s3"]``) and by integer index
    (``report[2]``, in section order).
    """

    def __init__(
        self, path: str | Path, *, name: str | None = None, parser: G2KParser | None = None
    ) -> None:
        self.path = Path(path)
        self.name = name or self.path.stem
        self.parser = parser or G2KParser()
        self._data = self.parser.parse(str(self.path))

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
