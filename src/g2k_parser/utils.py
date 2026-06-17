import re
import unicodedata

HEADERS = re.compile(r"^\*+$\n^\*{5}(.*)\*{5}$\n^\*+$", re.MULTILINE)


def strip_accents(s: str) -> str:
    """strip accents to avoide error on specific call"""
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


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
