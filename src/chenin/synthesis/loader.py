import warnings
from pathlib import Path

from chenin.g2k_parser import Report

from .layers import natural_key


def load_reports(directory: str | Path, pattern: str = "*.txt") -> dict[str, Report]:
    """Parse every G2K report in a directory, keyed by file stem.

    The stem is the report key used everywhere else (``Report.name``,
    ``SampleSpec.report``, the app's report selector), and the mapping is
    natural-sorted so ``NOI_S_2`` comes before ``NOI_S_10``.

    A directory can hold unrelated ``.txt`` files, so files that do not parse as a G2K
    report are skipped — but never silently: each one is warned about, because a
    report vanishing from a synthesis is a data-integrity problem, not a detail.
    """
    root = Path(directory)
    if not root.is_dir():
        raise NotADirectoryError(f"not a directory: {root}")

    paths = sorted(root.glob(pattern), key=lambda p: natural_key(p.stem))

    reports: dict[str, Report] = {}
    for path in paths:
        try:
            reports[path.stem] = Report(path, name=path.stem)
        except (ValueError, KeyError) as e:
            warnings.warn(f"skipped {path.name}: {e}", stacklevel=2)

    if not reports:
        raise FileNotFoundError(f"no parsable G2K report matching '{pattern}' in {root}")

    return reports
