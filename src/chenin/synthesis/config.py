"""Build-file model: parsing, validation and serialisation of the TOML build file.

A build file is the single entry point of a synthesis: it references the ordered
sample list (report file + layer depths, data absent from the G2K reports) and the
synthesis format (nuclides and columns).
"""

import tomllib
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, fields
from pathlib import Path
from typing import IO


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
    the G2K report and must come from the build file.
    """

    name: str
    depth_top: float
    depth_bot: float


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
    """A validated build configuration: samples + synthesis format in one file."""

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
    def from_toml(cls, file: str | Path | IO[bytes]) -> BuildConfig:
        """Load and validate a configuration from a TOML path or binary file object."""
        if isinstance(file, (str, Path)):
            with open(file, "rb") as f:
                raw = tomllib.load(f)
        else:
            raw = tomllib.load(file)
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
            raise ValueError("config has no [nuclides.*] entries")
        nuclides = {key: _parse_nuclide(key, spec) for key, spec in nuclides_raw.items()}

        columns_raw = raw.get("columns", {})
        if not columns_raw:
            raise ValueError("config has no [columns.*] entries")
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

    def to_toml(self) -> str:
        """Serialise back to a build-file TOML string (round-trips ``from_toml``)."""
        lines = [f"title = {_toml_str(self.title)}"]
        if self.description:
            lines.append(f"description = {_toml_str(self.description)}")
        if self.base_path:
            lines.append(f"base_path = {_toml_str(self.base_path)}")

        for sample in self.samples:
            lines += [
                "",
                "[[samples]]",
                f"name = {_toml_str(sample.name)}",
                f"depth_top = {sample.depth_top}",
                f"depth_bot = {sample.depth_bot}",
            ]

        meta_items = [
            (key, getattr(self.metadata, key))
            for key in ("base_year", "taux_sedimentation", "coring_yr")
            if getattr(self.metadata, key) is not None
        ]
        if meta_items:
            lines += ["", "[metadata]"]
            lines += [f"{key} = {value}" for key, value in meta_items]

        for key, nuclide in self.nuclides.items():
            peaks = ", ".join(
                f"{{ nuclide = {_toml_str(p.nuclide)}, energy = {p.energy} }}"
                for p in nuclide.peaks
            )
            lines += ["", f"[nuclides.{key}]", f"peaks = [{peaks}]"]

        for column in self.columns:
            lines += ["", f"[columns.{column.key}]", f"name = {_toml_str(column.name)}"]
            if column.source is not None:
                lines.append(f"source = {_toml_str(column.source)}")
            else:
                lines.append(f"formula = {_toml_str(column.formula)}")

        return "\n".join(lines) + "\n"


def _opt_float(value) -> float | None:
    """Coerce an optional TOML number to float (TOML ints stay int otherwise)."""
    return None if value is None else float(value)


def _toml_str(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _require_identifier(kind: str, key: str) -> None:
    """A nuclide/column key must be a valid identifier so formulas can reference it."""
    if not key.isidentifier():
        raise ValueError(f"{kind} key '{key}' is not a valid identifier")


def _parse_sample(spec: dict) -> SampleSpec:
    """Validate and build a single SampleSpec, raising clear errors."""
    name = spec.get("name")
    if not name:
        raise ValueError("a sample is missing its 'name'")
    for field in ("depth_top", "depth_bot"):
        if field not in spec:
            raise ValueError(f"sample '{name}' is missing '{field}'")

    depth_top = float(spec["depth_top"])
    depth_bot = float(spec["depth_bot"])
    if depth_bot < depth_top:
        raise ValueError(
            f"sample '{name}' has depth_bot ({depth_bot}) < depth_top ({depth_top})"
        )

    return SampleSpec(name=name, depth_top=depth_top, depth_bot=depth_bot)


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
