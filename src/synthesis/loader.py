from pathlib import Path

from g2k_parser import Report

from .config import BuildConfig


def load_reports(config: BuildConfig, base_dir: Path) -> dict[str, Report]:
    """Build one Report per sample, read from disk under ``base_path``.

    ``base_path`` (from the build file) is resolved relative to ``base_dir`` — the
    directory of the build file for the CLI, or the working directory for Streamlit.
    Reports are keyed by the sample ``name`` as written in the build file.
    """
    root = (base_dir / (config.base_path or ".")).resolve()

    reports: dict[str, Report] = {}
    for sample in config.samples:
        path = root / sample.name
        if not path.exists():
            raise FileNotFoundError(
                f"rapport introuvable pour l'échantillon '{sample.name}' : {path}"
            )
        # File already on disk: local and temp paths are the same.
        reports[sample.name] = Report(str(path), str(path))

    return reports
