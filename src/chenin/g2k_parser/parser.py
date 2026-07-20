import pandas as pd

from ._sections import (
    extract_s1,
    extract_s2_data,
    extract_s2_header,
    extract_s3_data,
    extract_s3_header,
    extract_s4_nucleides_data,
    extract_s4_nucleides_header,
    extract_s4_pics_data,
    extract_s4_pics_header,
    extract_s5_data,
    extract_s5_header,
    extract_s6_data,
    extract_s6_header,
)
from .utils import normalize_columns, split_sections


class G2KParser:
    """Parse a Génie 2000 ``.txt`` report into its constituent sections.

    Splits the report on its ``*****TITLE*****`` banners, then extracts a header
    and a data table from each of the six sections.
    """

    def parse(self, path: str) -> dict[str, pd.DataFrame]:
        """Parse the report at ``path`` into a dict of section name -> DataFrame."""
        with open(path) as f:
            content = f.read()

        titles, sections = split_sections(content)

        s4_raw = sections[titles[3]]
        s4_nucl_header = extract_s4_nucleides_header(s4_raw)
        s4_pics_header = extract_s4_pics_header(s4_raw)

        # s1 keys come straight from the report (dynamic), so they still need
        # accent stripping. s2-s6 column names are static ASCII constants from
        # `columns`, so no post-hoc normalization is required.
        return {
            "s1": normalize_columns(extract_s1(sections[titles[0]])),
            "s2": extract_s2_data(sections[titles[1]], extract_s2_header(sections[titles[1]])),
            "s3": extract_s3_data(sections[titles[2]], extract_s3_header(sections[titles[2]])),
            "s4_nucleides": extract_s4_nucleides_data(s4_raw, s4_nucl_header),
            "s4_pics": extract_s4_pics_data(s4_raw, s4_pics_header),
            "s5": extract_s5_data(sections[titles[4]], extract_s5_header(sections[titles[4]])),
            "s6": extract_s6_data(sections[titles[5]], extract_s6_header(sections[titles[5]])),
        }
