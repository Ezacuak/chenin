import pytest
import pandas as pd
from pathlib import Path
from src.extraction import Report, S2Extractor


@pytest.fixture
def rgu_report():
    report_path = Path(__file__).parent.parent / "data" / "rapport-RGU_3cm.txt"
    if report_path.exists():
        return Report.from_file(str(report_path))
    return None


def test_s2_extraction_returns_dataframe(rgu_report):
    if rgu_report is None:
        pytest.skip("Sample report not found")
    df = rgu_report.extract_s2()
    assert isinstance(df, pd.DataFrame)


def test_s2_extraction_has_correct_columns(rgu_report):
    if rgu_report is None:
        pytest.skip("Sample report not found")
    df = rgu_report.extract_s2()
    expected_columns = [
        "Numéro du pic",
        "Début (canaux)",
        "Fin (canaux)",
        "Centroïde",
        "Energie (keV)",
        "FWHM (keV)",
        "Surface",
        "Incert.",
        "Fond sous le pic",
    ]
    assert list(df.columns) == expected_columns


def test_s2_extraction_has_expected_row_count(rgu_report):
    if rgu_report is None:
        pytest.skip("Sample report not found")
    df = rgu_report.extract_s2()
    assert len(df) == 186


def test_s2_data_types(rgu_report):
    if rgu_report is None:
        pytest.skip("Sample report not found")
    df = rgu_report.extract_s2()
    numeric_columns = df.columns.tolist()
    for col in numeric_columns:
        assert pd.api.types.is_numeric_dtype(df[col])


def test_s2_no_null_values_in_key_columns(rgu_report):
    if rgu_report is None:
        pytest.skip("Sample report not found")
    df = rgu_report.extract_s2()
    assert not df["Numéro du pic"].isna().any()
    assert not df["Energie (keV)"].isna().any()
    assert not df["Surface"].isna().any()
