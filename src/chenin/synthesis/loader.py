from pathlib import Path

from chenin.g2k_parser import Report

from .config import BuildConfig


def load_reports(config: BuildConfig, base_dir: Path) -> dict[str, Report]:
    """Build one Report per sample, read from disk under ``base_path``.

    ``base_path`` (from the build file) is resolved relative to ``base_dir`` — the
    directory of the build file for the CLI, or the working directory for the app.
    Reports are keyed by the sample ``name`` as written in the build file.
    """
    root = (base_dir / (config.base_path or ".")).resolve()

    reports: dict[str, Report] = {}
    for sample in config.samples:
        path = root / sample.name
        if not path.exists():
            raise FileNotFoundError(f"report not found for sample '{sample.name}': {path}")
        reports[sample.name] = Report(path, name=sample.name)

    return reports
