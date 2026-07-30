from pathlib import Path

import pandas as pd
import pytest

from chenin.g2k_parser import columns as C

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "NOIR24-01"

requires_data = pytest.mark.skipif(
    not DATA_DIR.is_dir(), reason=f"sample core data not available at {DATA_DIR}"
)


@pytest.fixture
def s3():
    """A minimal section-3 frame: two PB-214 lines and one CS-137 line.

    Uncertainties are chosen so the inverse-variance weighted mean of the two PB-214
    lines is easy to check by hand.
    """
    return pd.DataFrame(
        {
            C.NUCLEIDE: ["PB-214", "PB-214", "CS-137"],
            C.ENERGIE_KEV: [295.21, 351.92, 661.66],
            C.ACTIVITE_MBQ: [100.0, 120.0, 50.0],
            C.INCERT_MBQ: [10.0, 10.0, 5.0],
        }
    )


class FakeReport(dict):
    """Just enough of Report for the builder: ``report["s3"]``."""

    def __init__(self, section3: pd.DataFrame, name: str = "fake"):
        super().__init__(s3=section3)
        self.name = name
