import tomllib
from dataclasses import dataclass, field
from io import BufferedReader

from streamlit.runtime.uploaded_file_manager import UploadedFile

PROVIDERS = ("report", "mean", "calculated")


@dataclass(frozen=True)
class Peak:
    """A single gamma peak referenced by nuclide name and energy (keV)."""

    nuclide: str
    energy: float


@dataclass(frozen=True)
class ColumnSpec:
    """How to compute one element column of the synthesis."""

    key: str
    name: str
    provider: str
    energy: float | None = None
    peaks: list[Peak] = field(default_factory=list)
    formula: str | None = None


@dataclass(frozen=True)
class MetadataSpec:
    """Sample-level metadata used to fill non-activity columns."""

    base_year: float | None = None
    taux_sedimentation: float | None = None
    epaisseur: float | None = None


@dataclass(frozen=True)
class SynthesisConfig:
    """A validated synthesis configuration."""

    title: str
    metadata: MetadataSpec
    columns: list[ColumnSpec]

    @classmethod
    def from_toml(cls, file: UploadedFile) -> "SynthesisConfig":
        """Load and validate a configuration from a TOML file."""

        raw = tomllib.load(file)
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict) -> "SynthesisConfig":
        """Build and validate a configuration from a parsed mapping."""
        meta_raw = raw.get("metadata", {})
        metadata = MetadataSpec(
            base_year=meta_raw.get("base_year"),
            taux_sedimentation=meta_raw.get("taux_sedimentation"),
            epaisseur=meta_raw.get("epaisseur"),
        )

        columns_raw = raw.get("columns", {})
        if not columns_raw:
            raise ValueError("config has no [columns.*] entries")

        columns = [_parse_column(key, spec) for key, spec in columns_raw.items()]

        return cls(
            title=raw.get("title", "Synthese"),
            metadata=metadata,
            columns=columns,
        )


def _parse_column(key: str, spec: dict) -> ColumnSpec:
    """Validate and build a single ColumnSpec, raising clear errors."""
    name = spec.get("name")
    if not name:
        raise ValueError(f"column '{key}' is missing a 'name'")

    provider = spec.get("provider", "report")
    if provider not in PROVIDERS:
        raise ValueError(
            f"column '{key}' has invalid provider '{provider}' "
            f"(expected one of {', '.join(PROVIDERS)})"
        )

    peaks = [
        Peak(nuclide=p["nuclide"], energy=float(p["energy"]))
        for p in spec.get("peaks", [])
    ]
    formula = spec.get("formula")

    if provider == "mean" and not peaks:
        raise ValueError(f"column '{key}' (provider 'mean') needs a non-empty 'peaks'")
    if provider == "calculated" and not formula:
        raise ValueError(f"column '{key}' (provider 'calculated') needs a 'formula'")

    energy = spec.get("energy")
    return ColumnSpec(
        key=key,
        name=name,
        provider=provider,
        energy=float(energy) if energy is not None else None,
        peaks=peaks,
        formula=formula,
    )
