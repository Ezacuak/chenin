import re
import unicodedata

HEADERS = re.compile(r"^\*+$\n^\*{5}(.*)\*{5}$\n^\*+$", re.MULTILINE)

# Element symbol and mass number, in either order, separated by optional space/dash.
NUCLIDE = re.compile(r"^(\d{1,3})?[\s-]*([A-Za-z]{1,2})[\s-]*(\d{1,3})?$")


def strip_accents(s: str) -> str:
    """strip accents to avoide error on specific call"""
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def format_nuclide(name: str) -> str:
    """format a nuclide name to canonical G2K form, e.g. "210pb" or "Pb-210" -> "PB-210" """
    match = NUCLIDE.match(name.strip())
    if not match:
        raise ValueError(f"'{name}' is not a recognizable nuclide name")

    mass = match.group(1) or match.group(3)
    if mass is None:
        raise ValueError(f"'{name}' is missing a mass number")

    return f"{match.group(2).upper()}-{mass}"


def normalize_columns(df):
    """strip all accents of dataframe columns names"""
    df.columns = [strip_accents(col) for col in df.columns]
    return df


def split_sections(content: str):
    """split content of G2K report to sections"""
    sections_titles = []
    sections_content = {}

    matches = list(HEADERS.finditer(content))
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        sections_titles.append(title)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        sections_content[title] = content[start:end].strip()

    return sections_titles, sections_content
