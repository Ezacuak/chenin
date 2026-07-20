"""Build model: parse and validate the synthesis inputs.

A synthesis is driven by two scientist-friendly tables:

- a **roadmap** CSV/Excel (per core) — the ordered sample list (report file +
  layer depths + density), the data absent from the G2K reports;
- a **synthesis template** CSV — a compact *wide* table whose header row gives the
  output column names and whose single second row gives each column's method
  (gamma peaks or an arithmetic formula). A lab default ships with the package.

Both are parsed into the same validated :class:`BuildConfig`; everything
downstream depends only on that object, not on the input format.
"""

import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, fields
from importlib import resources
from pathlib import Path
from typing import IO

import pandas as pd

# --- Roadmap column headers (as written by scientists) --- #
RM_CORE = "LSM Code"
RM_SAMPLE = "Sample Code"
RM_TOP = "Depth Top"
RM_BOT = "Depth Bot"
RM_DBD = "DBD"
RM_REPORT = "G2K Report"


@dataclass(frozen=True)
class Peak:
    """A single gamma peak referenced by nuclide name and energy (keV)."""

    nuclide: str
    energy: float


@dataclass(frozen=True)
class NuclideSpec:
    """A reusable measurement source: a nuclide read from one or more gamma lines.

    The activity is the inverse-variance weighted mean over ``peaks``. Each peak must
    carry an explicit energy (the identification line is always known).
    """

    key: str
    peaks: list[Peak]


@dataclass(frozen=True)
class ColumnSpec:
    """One displayed column of the synthesis.

    Exactly one of ``source`` (a nuclide key) or ``formula`` (arithmetic over nuclide
    keys) is set.
    """

    key: str
    name: str
    source: str | None = None
    formula: str | None = None


@dataclass(frozen=True)
class SampleSpec:
    """One sediment sample: a report file plus its layer geometry (cm).

    ``depth_top``/``depth_bot`` are the missing data source — they are not present in
    the G2K report and must come from the roadmap. ``name`` (the report file) may be
    ``None`` for a planned-but-unmeasured layer, kept as a depth-only row.
    """

    name: str | None
    depth_top: float
    depth_bot: float
    sample_code: str | None = None
    dbd: float | None = None


@dataclass(frozen=True)
class MetadataSpec:
    """Core-level metadata used to fill non-activity columns.

    ``base_year``/``taux_sedimentation`` drive the optional constant-rate ``Age``
    column; ``coring_yr`` records when the core was taken (kept for downstream
    age-depth tools).
    """

    base_year: float | None = None
    taux_sedimentation: float | None = None
    coring_yr: float | None = None


@dataclass(frozen=True)
class BuildConfig(Mapping):
    """A validated build configuration: samples + synthesis format."""

    title: str
    description: str | None
    base_path: str | None
    samples: list[SampleSpec]
    metadata: MetadataSpec
    nuclides: dict[str, NuclideSpec]
    columns: list[ColumnSpec]

    def __getitem__(self, key: str):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key) from None

    def __iter__(self) -> Iterator[str]:
        return (f.name for f in fields(self))

    def __len__(self) -> int:
        return len(fields(self))

    @classmethod
    def from_roadmap(
        cls,
        roadmap: str | Path | IO,
        template: str | Path | IO | None = None,
    ) -> BuildConfig:
        """Build a configuration from a roadmap file and a synthesis template.

        ``roadmap`` is a CSV/Excel sample list; ``template`` is a wide synthesis
        template CSV — when ``None`` the packaged lab default is used.
        """
        samples, core_id = parse_roadmap(roadmap)
        if template is None:
            ref = resources.files("chenin.synthesis") / "default_template.csv"
            with resources.as_file(ref) as default_path:
                nuclides, columns = parse_template(default_path)
        else:
            nuclides, columns = parse_template(template)

        raw = {
            "title": core_id or "Synthesis",
            "samples": samples,
            "nuclides": nuclides,
            "columns": columns,
        }
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict) -> BuildConfig:
        samples = [_parse_sample(spec) for spec in raw.get("samples", [])]

        meta_raw = raw.get("metadata", {})
        metadata = MetadataSpec(
            base_year=_opt_float(meta_raw.get("base_year")),
            taux_sedimentation=_opt_float(meta_raw.get("taux_sedimentation")),
            coring_yr=_opt_float(meta_raw.get("coring_yr")),
        )

        nuclides_raw = raw.get("nuclides", {})
        if not nuclides_raw:
            raise ValueError("config has no nuclide sources")
        nuclides = {key: _parse_nuclide(key, spec) for key, spec in nuclides_raw.items()}

        columns_raw = raw.get("columns", {})
        if not columns_raw:
            raise ValueError("config has no output columns")
        columns = [_parse_column(key, spec, nuclides) for key, spec in columns_raw.items()]

        return cls(
            title=raw.get("title", "Synthesis"),
            description=raw.get("description"),
            base_path=raw.get("base_path"),
            samples=samples,
            metadata=metadata,
            nuclides=nuclides,
            columns=columns,
        )


# --- Roadmap parsing --- #


def parse_roadmap(file: str | Path | IO) -> tuple[list[dict], str | None]:
    """Read a roadmap CSV/Excel into sample dicts and the core id.

    Rows with an empty ``G2K Report`` are kept with ``name=None`` (depth-only).
    """
    df = _read_table(file, skipinitialspace=True)
    _require_columns(df, [RM_TOP, RM_BOT])

    samples: list[dict] = []
    for row in df.to_dict("records"):
        top = _cell_float(row.get(RM_TOP))
        bot = _cell_float(row.get(RM_BOT))
        if top is None and bot is None:
            continue  # blank trailing line
        samples.append(
            {
                "name": _cell_str(row.get(RM_REPORT)) or None,
                "depth_top": top,
                "depth_bot": bot,
                "sample_code": _cell_str(row.get(RM_SAMPLE)) or None,
                "dbd": _cell_float(row.get(RM_DBD)),
            }
        )

    core_id = None
    if RM_CORE in df.columns and len(df):
        core_id = _cell_str(df[RM_CORE].iloc[0]) or None

    return samples, core_id


# --- Template parsing --- #

_PEAK_SEP = ";"
_REF_PATTERN = re.compile(r"\[([^\]]+)\]")


def parse_template(file: str | Path | IO) -> tuple[dict[str, dict], dict[str, dict]]:
    """Read a wide synthesis template into ``(nuclides, columns)`` raw dicts.

    The header row holds display names; the single second row holds each column's
    method: gamma peaks (``NUCLIDE@energy``, ``;``-separated for a weighted mean) or
    an ``=`` formula over other columns referenced as ``[Name]``.
    """
    df = _read_table(file)
    if df.empty:
        raise ValueError("synthesis template has no method row")
    method_row = df.iloc[0]

    nuclides: dict[str, dict] = {}
    columns: dict[str, dict] = {}
    for name in df.columns:
        display = str(name).strip()
        if not display or display.lower().startswith("unnamed"):
            continue
        method = _cell_str(method_row[name])
        if not method:
            raise ValueError(f"column '{display}' has no method")

        key = _slug(display)
        if method.startswith("="):
            formula = _REF_PATTERN.sub(lambda m: _slug(m.group(1)), method[1:].strip())
            columns[key] = {"name": display, "formula": formula}
        else:
            nuclides[key] = {"peaks": _parse_peaks(display, method)}
            columns[key] = {"name": display, "source": key}

    if not nuclides:
        raise ValueError("synthesis template has no measured (peak) columns")
    return nuclides, columns


def _parse_peaks(display: str, method: str) -> list[dict]:
    peaks: list[dict] = []
    for item in method.split(_PEAK_SEP):
        item = item.strip()
        if not item:
            continue
        if "@" not in item:
            raise ValueError(f"column '{display}': peak '{item}' must be NUCLIDE@energy")
        nuclide, _, energy = item.partition("@")
        try:
            peaks.append({"nuclide": nuclide.strip(), "energy": float(energy)})
        except ValueError:
            raise ValueError(f"column '{display}': peak '{item}' has an invalid energy") from None
    if not peaks:
        raise ValueError(f"column '{display}' has no peaks")
    return peaks


# --- Shared helpers --- #


def _read_table(file: str | Path | IO, *, skipinitialspace: bool = False) -> pd.DataFrame:
    """Read a CSV or Excel table as strings, choosing the reader by extension."""
    name = str(getattr(file, "name", file) or "").lower()
    if name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file, dtype=str)
    else:
        df = pd.read_csv(file, dtype=str, skipinitialspace=skipinitialspace)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _require_columns(df: pd.DataFrame, required: list[str]) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"roadmap is missing column(s): {', '.join(missing)}")


def _cell_str(value) -> str:
    """Coerce a cell to a stripped string, treating NaN/None as empty."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, str):
        return value.strip()
    if pd.isna(value):
        return ""
    return str(value).strip()


def _cell_float(value) -> float | None:
    """Coerce a cell to float, treating missing/blank/NaN as None."""
    text = _cell_str(value)
    if not text:
        return None
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def _slug(name: str) -> str:
    """Turn a display name into a valid identifier key (e.g. 'PB-210' -> 'pb_210')."""
    s = re.sub(r"[^0-9a-zA-Z]+", "_", name.strip().lower()).strip("_")
    if not s:
        s = "col"
    if s[0].isdigit():
        s = "_" + s
    return s


def _opt_float(value) -> float | None:
    """Coerce an optional number to float."""
    return None if value is None else float(value)


def _require_identifier(kind: str, key: str) -> None:
    """A nuclide/column key must be a valid identifier so formulas can reference it."""
    if not key.isidentifier():
        raise ValueError(f"{kind} key '{key}' is not a valid identifier")


def _parse_sample(spec: dict) -> SampleSpec:
    """Validate and build a single SampleSpec, raising clear errors."""
    for field in ("depth_top", "depth_bot"):
        if spec.get(field) is None:
            raise ValueError(f"a sample is missing '{field}'")

    depth_top = float(spec["depth_top"])
    depth_bot = float(spec["depth_bot"])
    if depth_bot < depth_top:
        raise ValueError(
            f"sample at depth {depth_top} has depth_bot ({depth_bot}) < depth_top ({depth_top})"
        )

    return SampleSpec(
        name=spec.get("name") or None,
        depth_top=depth_top,
        depth_bot=depth_bot,
        sample_code=spec.get("sample_code") or None,
        dbd=_opt_float(spec.get("dbd")),
    )


def _parse_nuclide(key: str, spec: dict) -> NuclideSpec:
    """Validate and build a single NuclideSpec, raising clear errors."""
    _require_identifier("nuclide", key)

    peaks_raw = spec.get("peaks")
    if not peaks_raw:
        raise ValueError(f"nuclide '{key}' needs a non-empty 'peaks'")

    peaks = []
    for p in peaks_raw:
        if "nuclide" not in p:
            raise ValueError(f"nuclide '{key}' has a peak missing 'nuclide'")
        if "energy" not in p:
            raise ValueError(f"nuclide '{key}' has a peak missing 'energy'")
        peaks.append(Peak(nuclide=p["nuclide"], energy=float(p["energy"])))

    return NuclideSpec(key=key, peaks=peaks)


def _parse_column(key: str, spec: dict, nuclides: dict[str, NuclideSpec]) -> ColumnSpec:
    """Validate and build a single ColumnSpec, raising clear errors."""
    _require_identifier("column", key)

    name = spec.get("name")
    if not name:
        raise ValueError(f"column '{key}' is missing a 'name'")

    source = spec.get("source")
    formula = spec.get("formula")
    if (source is None) == (formula is None):
        raise ValueError(f"column '{key}' must have exactly one of 'source' or 'formula'")
    if source is not None and source not in nuclides:
        raise ValueError(f"column '{key}' references unknown nuclide '{source}'")

    return ColumnSpec(key=key, name=name, source=source, formula=formula)
