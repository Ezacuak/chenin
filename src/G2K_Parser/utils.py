import re
import unicodedata

###################################################
#                      Utils                      #
###################################################


class Utils:
    HEADERS = re.compile(r"^\*+$\n^\*{5}(.*)\*{5}$\n^\*+$", re.MULTILINE)

    @staticmethod
    def strip_accents(s):
        return "".join(
            c
            for c in unicodedata.normalize("NFD", s)
            if unicodedata.category(c) != "Mn"
        )

    @staticmethod
    def normalize_columns(df):
        df.columns = [Utils.strip_accents(col) for col in df.columns]

        return df

    @staticmethod
    def split_sections(content):
        sections_titles = []
        sections_content = {}

        matches = list(Utils.HEADERS.finditer(content))
        for i, match in enumerate(matches):
            title = match.group(1).strip()
            sections_titles.append(title)
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            sections_content[title] = content[start:end].strip()

        return sections_titles, sections_content
