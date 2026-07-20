from pathlib import Path

from chenin.g2k_parser import Report

from .config import BuildConfig


def load_reports(config: BuildConfig, base_dir: Path) -> dict[str, Report]:
    """Build one Report per sample with a report file, read from disk.

    Report files sit next to the roadmap, so ``base_dir`` (the roadmap's folder for
    the CLI, or the working directory for the app) is the report root. Samples with no
    report file (depth-only rows) are skipped. Reports are keyed by the sample ``name``.
    """
    root = (base_dir / (config.base_path or ".")).resolve()

    reports: dict[str, Report] = {}
    for sample in config.samples:
        if not sample.name:
            continue
        path = root / sample.name
        if not path.exists():
            raise FileNotFoundError(f"report not found for sample '{sample.name}': {path}")
        reports[sample.name] = Report(path, name=sample.name)

    return reports
