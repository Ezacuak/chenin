"""Turn a list of reports into core layers.

G2K reports carry no depth, so the layer geometry has to come from somewhere else.
Cores are usually sliced at a constant step, and the slice number is written into the
report file name (``NOI_S_13`` is the 13th slice), so the depths can be *generated*
and then corrected by hand where the core is irregular.

This is the single implementation of that rule: the app's "Core layers" grid and the
``chenin synthesis`` CLI both call :func:`slice_samples`, so they cannot drift apart.
"""

import re
from collections.abc import Iterable

from .config import SampleSpec

_TRAILING_INDEX = re.compile(r"(\d+)\s*$")


def index_from_name(name: str) -> int | None:
    """The slice number written at the end of a report name, if any.

    ``NOI_S_13`` -> ``13``, ``rapport-RGU_3cm`` -> ``None`` (the trailing token is a
    unit, not an index — anything not ending in digits is unnumbered).
    """
    match = _TRAILING_INDEX.search(name)
    return int(match.group(1)) if match else None


def natural_key(name: str) -> tuple:
    """Sort key that orders ``NOI_S_2`` before ``NOI_S_10``."""
    return tuple(
        int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", name)
    )


def slice_samples(
    report_names: Iterable[str],
    *,
    start: float = 0.0,
    thickness: float = 1.0,
    use_name_index: bool = True,
    dbd: float | None = None,
) -> list[SampleSpec]:
    """Generate one :class:`SampleSpec` per report from a constant slicing rule.

    With ``use_name_index`` (the default) the depth follows the number in the file
    name: ``start + (n - 1) * thickness``. That keeps a core with missing slices
    honest — if slice 12 was never measured, slice 13 still sits at its true depth
    instead of moving up to fill the hole. Reports with no trailing number fall back
    to their position in the natural-sorted list.

    With ``use_name_index=False`` the reports are simply stacked contiguously in
    natural-sorted order.
    """
    if thickness <= 0:
        raise ValueError(f"thickness must be positive, got {thickness}")

    names = sorted(report_names, key=natural_key)

    samples: list[SampleSpec] = []
    for position, name in enumerate(names, start=1):
        index = index_from_name(name) if use_name_index else None
        depth_top = start + ((index or position) - 1) * thickness
        samples.append(
            SampleSpec(
                report=name,
                depth_top=depth_top,
                depth_bot=depth_top + thickness,
                sample_code=name,
                dbd=dbd,
            )
        )
    return samples


def contiguity_gaps(samples: Iterable[SampleSpec]) -> list[tuple[float, float]]:
    """Depth intervals not covered by any sample, in order.

    A core with unmeasured slices is perfectly legitimate — this reports the holes so
    the UI can warn about them rather than reject them.
    """
    ordered = sorted(samples, key=lambda s: s.depth_top)
    gaps: list[tuple[float, float]] = []
    for previous, current in zip(ordered, ordered[1:], strict=False):
        if current.depth_top > previous.depth_bot:
            gaps.append((previous.depth_bot, current.depth_top))
    return gaps


def overlaps(samples: Iterable[SampleSpec]) -> list[tuple[SampleSpec, SampleSpec]]:
    """Pairs of consecutive samples whose depth ranges overlap."""
    ordered = sorted(samples, key=lambda s: s.depth_top)
    return [
        (previous, current)
        for previous, current in zip(ordered, ordered[1:], strict=False)
        if current.depth_top < previous.depth_bot
    ]
