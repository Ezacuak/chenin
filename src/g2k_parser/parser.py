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
    """
    Implement Parser class to extract G2K report

    Extract 6 sections from a report file (`txt` format)
    """

    def parse(self, path: str) -> dict[str, pd.DataFrame]:
        """
        Parse the report in section.

        Then extract header and data from each section to a dictionary of Pandas DataFrame.
        """
        content = ""

        try:
            with open(path) as f:
                content = f.read()
        except OSError as e:
            print(f"Error while opening the file: {e}")

        titles, sections = split_sections(content)

        s4_raw = sections[titles[3]]
        s4_nucl_header = extract_s4_nucleides_header(s4_raw)
        s4_pics_header = extract_s4_pics_header(s4_raw)

        # s1 keys come straight from the report (dynamic), so they still need
        # accent stripping. s2-s6 column names are static ASCII constants from
        # `columns`, so no post-hoc normalization is required.
        return {
            "s1": normalize_columns(extract_s1(sections[titles[0]])),
            "s2": extract_s2_data(
                sections[titles[1]], extract_s2_header(sections[titles[1]])
            ),
            "s3": extract_s3_data(
                sections[titles[2]], extract_s3_header(sections[titles[2]])
            ),
            "s4_nucleides": extract_s4_nucleides_data(s4_raw, s4_nucl_header),
            "s4_pics": extract_s4_pics_data(s4_raw, s4_pics_header),
            "s5": extract_s5_data(
                sections[titles[4]], extract_s5_header(sections[titles[4]])
            ),
            "s6": extract_s6_data(
                sections[titles[5]], extract_s6_header(sections[titles[5]])
            ),
        }
