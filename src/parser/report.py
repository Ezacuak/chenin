from ._sections import (
    extract_data_1_s4,
    extract_data_2_s4,
    extract_data_s2,
    extract_data_s3,
    extract_data_s5,
    extract_data_s6,
    extract_header_1_s4,
    extract_header_2_s4,
    extract_header_s2,
    extract_header_s3,
    extract_header_s5,
    extract_header_s6,
    extract_s1,
)
from .utils import normalize_columns, split_sections


def parse_report(path):
    with open(path) as f:
        content = f.read()

    titles, sections = split_sections(content)

    data_s1 = extract_s1(sections[titles[0]])

    header_s2 = extract_header_s2(sections[titles[1]])
    data_s2 = extract_data_s2(sections[titles[1]], header_s2)

    header_s3 = extract_header_s3(sections[titles[2]])
    data_s3 = extract_data_s3(sections[titles[2]], header_s3)

    header_1_s4 = extract_header_1_s4(sections[titles[3]])
    header_2_s4 = extract_header_2_s4(sections[titles[3]])
    data_1_s4 = extract_data_1_s4(sections[titles[3]], header_1_s4)
    data_2_s4 = extract_data_2_s4(sections[titles[3]], header_2_s4)

    header_s5 = extract_header_s5(sections[titles[4]])
    data_s5 = extract_data_s5(sections[titles[4]], header_s5)

    header_s6 = extract_header_s6(sections[titles[5]])
    data_s6 = extract_data_s6(sections[titles[5]], header_s6)

    return {
        "s1": normalize_columns(data_s1),
        "s2": normalize_columns(data_s2),
        "s3": normalize_columns(data_s3),
        "s4_nucleides": normalize_columns(data_1_s4),
        "s4_pics": normalize_columns(data_2_s4),
        "s5": normalize_columns(data_s5),
        "s6": normalize_columns(data_s6),
    }
