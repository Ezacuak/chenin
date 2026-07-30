"""Build model: parse and validate the synthesis inputs.

A synthesis is driven by two things:

- a **sample list** — the ordered layers of the core, each one a report file plus its
  depths and density. This is the data absent from the G2K reports; it is entered in
  the app (Synthesis page, "Core layers") or generated from a slicing rule by
  :mod:`chenin.synthesis.layers`;
- a **synthesis template** CSV — a compact *wide* table whose header row gives the
  output column names and whose single second row gives each column's method (gamma
  peaks or an arithmetic formula). A lab default ships with the package.

Both end up in a validated :class:`BuildConfig`; everything downstream depends only on
that object, not on where the samples came from.
"""

import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, fields
from importlib import resources
from pathlib import Path
from typing import IO

import pandas as pd

# Geometry field -> output column name. The names are French because they feed
# SERAC and the lab's downstream workbooks; do not translate them.
# ``thickness`` is derived (depth_bot - depth_top), the rest are SampleSpec fields.
GEOMETRY_COLUMNS = {
    "sample_code": "Echantillon",
    "depth_top": "Profondeur",
    "thickness": "Epaisseur",
    "dbd": "DBD",
}


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

    Exactly one of ``source`` (a nuclide key), ``formula`` (arithmetic over nuclide
    keys) or ``geometry`` (a key of :data:`GEOMETRY_COLUMNS`) is set. Geometry columns
    are written as-is; the other two yield an ``Activite``/``Incertitude`` pair.
    """

    key: str
    name: str
    source: str | None = None
    formula: str | None = None
    geometry: str | None = None

    @property
    def is_geometry(self) -> bool:
        return self.geometry is not None


@dataclass(frozen=True)
class SampleSpec:
    """One sediment sample: a report plus its layer geometry (cm).

    ``depth_top``/``depth_bot`` are the missing data source — they are not present in
    the G2K report. ``report`` is the report key (its stem, matching ``Report.name``)
    and may be ``None`` for a planned-but-unmeasured layer, kept as a depth-only row.
    """

    report: str | None
    depth_top: float
    depth_bot: float
    sample_code: str | None = None
    dbd: float | None = None

    @property
    def thickness(self) -> float:
        return self.depth_bot - self.depth_top


def default_geometry_columns() -> list[ColumnSpec]:
    """The standard geometry columns, in output order."""
    return [
        ColumnSpec(key=field, name=name, geometry=field)
        for field, name in GEOMETRY_COLUMNS.items()
    ]


@dataclass(frozen=True)
class BuildConfig(Mapping):
    """A validated build configuration: samples + synthesis format.

    Validation runs on construction, so building the specs by hand (as the app does)
    is checked exactly like parsing them from a file.
    """

    title: str
    description: str | None
    samples: list[SampleSpec]
    nuclides: dict[str, NuclideSpec]
    columns: list[ColumnSpec]

    def __post_init__(self) -> None:
        if not self.nuclides:
            raise ValueError("config has no nuclide sources")
        if not self.columns:
            raise ValueError("config has no output columns")
        for column in self.columns:
            _validate_column(column, self.nuclides)

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
    def from_template(
        cls,
        template: str | Path | IO | None,
        samples: list[SampleSpec],
        *,
        title: str = "Synthesis",
        geometry: bool = True,
    ) -> BuildConfig:
        """Build a configuration from a synthesis template and a sample list.

        ``template`` is a wide synthesis template CSV — when ``None`` the packaged lab
        default is used. The standard geometry columns are prepended unless
        ``geometry`` is false.
        """
        if template is None:
            ref = resources.files("chenin.synthesis") / "default_template.csv"
            with resources.as_file(ref) as default_path:
                nuclides_raw, columns_raw = parse_template(default_path)
        else:
            nuclides_raw, columns_raw = parse_template(template)

        nuclides = {key: _parse_nuclide(key, spec) for key, spec in nuclides_raw.items()}
        columns = [_parse_column(key, spec) for key, spec in columns_raw.items()]
        if geometry:
            columns = default_geometry_columns() + columns

        return cls(
            title=title,
            description=None,
            samples=samples,
            nuclides=nuclides,
            columns=columns,
        )

    @classmethod
    def from_dict(cls, raw: dict) -> BuildConfig:
        """Build a configuration from nested raw dicts (the parsers' output shape)."""
        samples = [_parse_sample(spec) for spec in raw.get("samples", [])]
        nuclides = {key: _parse_nuclide(key, spec) for key, spec in raw.get("nuclides", {}).items()}
        columns = [_parse_column(key, spec) for key, spec in raw.get("columns", {}).items()]

        return cls(
            title=raw.get("title", "Synthesis"),
            description=raw.get("description"),
            samples=samples,
            nuclides=nuclides,
            columns=columns,
        )


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


def _read_table(file: str | Path | IO) -> pd.DataFrame:
    """Read a CSV or Excel table as strings, choosing the reader by extension."""
    name = str(getattr(file, "name", file) or "").lower()
    if name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file, dtype=str)
    else:
        df = pd.read_csv(file, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    return df


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
        report=spec.get("report") or None,
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


def _parse_column(key: str, spec: dict) -> ColumnSpec:
    """Build a single ColumnSpec from a raw dict; cross-checks happen in BuildConfig."""
    name = spec.get("name")
    if not name:
        raise ValueError(f"column '{key}' is missing a 'name'")

    return ColumnSpec(
        key=key,
        name=name,
        source=spec.get("source"),
        formula=spec.get("formula"),
        geometry=spec.get("geometry"),
    )


def _validate_column(column: ColumnSpec, nuclides: dict[str, NuclideSpec]) -> None:
    """A column has exactly one kind, and it must resolve against the config."""
    _require_identifier("column", column.key)

    kinds = [k for k in (column.source, column.formula, column.geometry) if k is not None]
    if len(kinds) != 1:
        raise ValueError(
            f"column '{column.key}' must have exactly one of 'source', 'formula' or 'geometry'"
        )

    if column.source is not None and column.source not in nuclides:
        raise ValueError(f"column '{column.key}' references unknown nuclide '{column.source}'")

    if column.geometry is not None and column.geometry not in GEOMETRY_COLUMNS:
        raise ValueError(
            f"column '{column.key}' references unknown geometry field '{column.geometry}' "
            f"(known: {', '.join(GEOMETRY_COLUMNS)})"
        )

    if column.formula is not None:
        for ref in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", column.formula):
            if ref not in nuclides:
                raise ValueError(
                    f"column '{column.key}' formula references unknown nuclide '{ref}'"
                )
