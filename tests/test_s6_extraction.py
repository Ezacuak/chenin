import pytest
import pandas as pd
from pathlib import Path
from src.extraction import Report, S6Extractor


@pytest.fixture
def rgu_report():
    report_path = Path(__file__).parent.parent / "data" / "rapport-RGU_3cm.txt"
    if report_path.exists():
        return Report.from_file(str(report_path))
    return None


def test_s6_extraction_returns_dataframe(rgu_report):
    if rgu_report is None:
        pytest.skip("Sample report not found")
    df = rgu_report.extract_s6()
    assert isinstance(df, pd.DataFrame)


def test_s6_extraction_not_empty(rgu_report):
    if rgu_report is None:
        pytest.skip("Sample report not found")
    df = rgu_report.extract_s6()
    assert len(df) > 0


def test_s6_has_required_columns(rgu_report):
    if rgu_report is None:
        pytest.skip("Sample report not found")
    df = rgu_report.extract_s6()
    assert "Marker" in df.columns
    assert "Nucleide" in df.columns
    assert len(df.columns) > 2


def test_s6_marker_values_valid(rgu_report):
    if rgu_report is None:
        pytest.skip("Sample report not found")
    df = rgu_report.extract_s6()
    valid_markers = {"+", ">", "?"}
    assert df["Marker"].isin(valid_markers).all()


def test_s6_nucleide_format(rgu_report):
    if rgu_report is None:
        pytest.skip("Sample report not found")
    df = rgu_report.extract_s6()
    import re
    pattern = re.compile(r"^[A-Z]{1,2}-\d{1,3}$")
    assert all(pattern.match(nuc) for nuc in df["Nucleide"].tolist())


def test_s6_numeric_columns(rgu_report):
    if rgu_report is None:
        pytest.skip("Sample report not found")
    df = rgu_report.extract_s6()
    numeric_cols = df.columns.tolist()[2:]
    for col in numeric_cols:
        assert pd.api.types.is_numeric_dtype(df[col])
