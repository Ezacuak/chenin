import argparse
import re
import unicodedata

import numpy as np
import pandas as pd

###################################################
#                      Regex                      #
###################################################
section_header_pattern = re.compile(r"^\*+$\n^\*{5}(.*)\*{5}$\n^\*+$", re.MULTILINE)
s1_kv_pattern = re.compile(r"^([^:]*):(.*)$", re.MULTILINE)
s2_header_pattern = re.compile(
    r"(Numéro)\s+(Début)\s+-\s+(Fin)\s+(Centroïde)\s+(Energie)\s+(FWHM)\s+(Surface)\s+(Incert\.)\s+(Fond sous)\s*\r?\n^\s*(du pic)\s+(\(canaux\))\s+(\(keV\))\s+(\(keV\))\s+(le pic)",
    re.MULTILINE,
)
s2_data_pattern = re.compile(
    r"^\s*([MmF]?)\s*(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+-\s*(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)",
    re.MULTILINE,
)
s3_header_pattern = re.compile(
    r"^\s+(Nom\sdu)\s+(Indice\sde)\s+(Energie)\s+(Intensité)\s+(Activité)\s+(Incert\.)$\n^\s+(nucléide)\s+(confiance)\s+(\W\w+\W)\s+(\W%\W)\s+(\WmBq\Wg\s+\W)\s+(\WmBq\Wg\s+\W)\n",
    re.MULTILINE,
)
s3_data_pattern = re.compile(
    r"^\s*([A-Z]{1,2}-\d{1,3})?\s*(\d+\.\d+)?\s*(\d+\.\d+)(\*?)\s*(@?)\s*(\d+\.\d+)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)$",
    re.MULTILINE,
)
s4_header_1_pattern = re.compile(
    r"^\s*(Nom du)\s+(Indice de)\s+(Activité moyenne)\s+(Incert\.)$\n^\s+(nucléide)\s+(confiance)\s+(pondérée)$\n^\s+(\WmBq\Wg\s+\W)\s+(\WmBq\Wg\s+\W)$",
    re.MULTILINE,
)
s4_header_2_pattern = re.compile(
    r"^\s*(Numéro)\s+(Energie)\s+(Intensité)\s+(Incert\.)\s+(Type)\s+(Nucléide)$\n^\s+(du pic)\s+(\WkeV\W)\s+(\Wcoups\Wsec\W)\s+(du pic)\s+(potentiel)$",
    re.MULTILINE,
)
s4_data_1_pattern = re.compile(
    r"^\s*(X?)\s+([A-Z]{1,2}-\d{1,3})\s*(@?)\s+(\d+\.\d+)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)?\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)?",
    re.MULTILINE,
)
s4_data_2_pattern = re.compile(
    r"^\s+([MmF])?\s*(\d+)\s+(\d+\.\d+)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+(\d+\.\d+)\s*(Sum|D-Esc\.|S-Esc\.|Tol\.)?\s*([A-Z]{1,2}-\d{1,3})?\s*$",
    re.MULTILINE,
)
s5_header_pattern = re.compile(
    r"^\s+(Nom\sdu)\s+(Energie)\s+(Intensité)\s*(LD\sEnergie)\s*(LD\snucléide)\s+(Activité)\s+(SD\sEnergie)$\n^\s+(nucléide)\s+(\WkeV\W)\s+(\W%\W)\s+(\WmBq\Wg\s+\W)\s+(\WmBq\Wg\s+\W)\s+(\WmBq\Wg\s+\W)\s+\s+(\WmBq\Wg\s+\W)$",
    re.MULTILINE,
)
s5_data_pattern = re.compile(
    r"^\s*(\+?)\s*(\??)\s*(>?)\s*([A-Z]{1,2}-\d{1,3})?\s+(\d+\.\d+)(\*?)\s*(@?)\s+(\d+\.\d+)\s+([+\-]?\d+(?:\.\d+)?(?:E[+\-]?\d+)?|Non\sCalc)(?:\s*([+\-]?\d+(?:\.\d+)?(?:E[+\-]?\d+)?))?\s+([+\-]?\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+([+\-]?\d+(?:\.\d+)?(?:E[+\-]?\d+)?)$",
    re.MULTILINE,
)
s6_header_pattern = re.compile(r"^\s+(.*)$\n^\s+(.*)$", re.MULTILINE)
s6_word_column_pattern = re.compile(r"([A-Za-zÀ-ÿ]+\.?)")
s6_nucleide_line_pattern = re.compile(
    r"^[+>?]\s+([A-Z]{1,2}-\d{1,3})\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)",
    re.MULTILINE,
)


###################################################
#                      Utils                      #
###################################################


def strip_accents(s):
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def normalize_columns(df):
    df.columns = [strip_accents(col) for col in df.columns]
    return df


def split_sections(content):
    sections_titles = []
    sections_content = {}

    matches = list(section_header_pattern.finditer(content))
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        sections_titles.append(title)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        sections_content[title] = content[start:end].strip()

    return sections_titles, sections_content


###################################################
#                    Sections                     #
###################################################


#############
# Section 1 #
#############
def extract_s1(content):
    matches = s1_kv_pattern.findall(content)
    return pd.DataFrame(
        {key.strip(): value.strip() for key, value in matches}, index=[0]
    )


#############
# Section 2 #
#############
def extract_header_s2(content):
    match = re.search(s2_header_pattern, content)
    if not match:
        return None
    return [
        "Marker",
        f"{match.group(1)} {match.group(9)}",
        f"{match.group(2)} {match.group(10)}",
        f"{match.group(3)} {match.group(11)}",
        match.group(4),
        f"{match.group(5)} {match.group(12)}",
        f"{match.group(6)} {match.group(13)}",
        match.group(7),
        match.group(8),
        f"{match.group(8)} {match.group(13)}",
    ]


def extract_data_s2(content, header):
    matches = re.findall(s2_data_pattern, content)
    df = pd.DataFrame(matches, columns=header)
    df["Marker"] = df["Marker"].replace("", np.nan)
    df = df.astype({"Marker": "category"})
    df = df.astype(
        {
            "Numéro Fond sous": "float64",
            "Début du pic": "float64",
            "Fin (canaux)": "float64",
            "Centroïde": "float64",
            "Energie (keV)": "float64",
            "FWHM (keV)": "float64",
            "Surface": "float64",
            "Incert.": "float64",
            "Incert. (keV)": "float64",
        }
    )
    return df


#############
# Section 3 #
#############


def extract_header_s3(content):
    matches = re.search(s3_header_pattern, content)
    if not matches:
        return None
    return [
        f"{matches.group(1)} {matches.group(7)}",
        f"{matches.group(2)} {matches.group(8)}",
        f"{matches.group(3)} {matches.group(9)}",
        "Marker *",
        "Marker @",
        f"{matches.group(4)} {matches.group(10)}",
        f"{matches.group(5)} {matches.group(11)}",
        f"{matches.group(6)} {matches.group(12)}",
    ]


def extract_data_s3(content, header):
    matches = re.findall(s3_data_pattern, content)
    df = pd.DataFrame(matches, columns=header)
    df["Nom du nucléide"] = df["Nom du nucléide"].replace("", np.nan)
    df["Indice de confiance"] = df["Indice de confiance"].replace("", np.nan)
    df = df.astype(
        {
            "Energie (keV)": "float64",
            "Intensité (%)": "float64",
            "Activité (mBq/g   )": "float64",
            "Incert. (mBq/g   )": "float64",
            "Indice de confiance": "float64",
        }
    )
    df = df.fillna({"Nom du nucléide": df["Nom du nucléide"].ffill()})
    df = df.astype(
        {"Nom du nucléide": "category", "Marker *": "bool", "Marker @": "bool"}
    )
    return df


#############
# Section 4 #
#############


def extract_header_1_s4(content):
    matches = re.search(s4_header_1_pattern, content)
    if not matches:
        return None
    return [
        "Marker (X)",
        f"{matches.group(1)} {matches.group(5)}",
        "Marker (@)",
        f"{matches.group(2)} {matches.group(6)}",
        f"{matches.group(3)} {matches.group(7)} {matches.group(8)}",
        f"{matches.group(4)} {matches.group(9)}",
    ]


def extract_header_2_s4(content):
    matches = re.search(s4_header_2_pattern, content)
    if not matches:
        return None
    return [
        "Marker (M/m/F)",
        f"{matches.group(1)} {matches.group(7)}",
        f"{matches.group(2)} {matches.group(8)}",
        f"{matches.group(3)} {matches.group(9)}",
        f"{matches.group(4)}",
        f"{matches.group(5)} {matches.group(10)}",
        f"{matches.group(6)} {matches.group(11)}",
    ]


def extract_data_1_s4(content, header):
    matches = re.findall(s4_data_1_pattern, content)
    df = pd.DataFrame(matches, columns=header)
    df = df.astype({"Marker (X)": "bool", "Marker (@)": "bool"})
    df["Activité moyenne pondérée (mBq/g   )"] = df[
        "Activité moyenne pondérée (mBq/g   )"
    ].replace("", np.nan)
    df["Incert. (mBq/g   )"] = df["Incert. (mBq/g   )"].replace("", np.nan)
    df = df.astype(
        {
            "Indice de confiance": "object",
            "Activité moyenne pondérée (mBq/g   )": "object",
            "Incert. (mBq/g   )": "object",
            "Nom du nucléide": "category",
        }
    )
    return df


def extract_data_2_s4(content, header):
    matches = re.findall(s4_data_2_pattern, content)
    df = pd.DataFrame(matches, columns=header)
    df["Marker (M/m/F)"] = df["Marker (M/m/F)"].replace("", np.nan)
    df["Type du pic"] = df["Type du pic"].replace("", np.nan)
    df["Nucléide potentiel"] = df["Nucléide potentiel"].replace("", np.nan)
    df = df.astype(
        {
            "Marker (M/m/F)": "category",
            "Type du pic": "category",
            "Nucléide potentiel": "category",
        }
    )
    df = df.astype(
        {
            "Numéro du pic": "float64",
            "Energie (keV)": "float64",
            "Intensité (coups/sec)": "float64",
            "Incert.": "float64",
        }
    )
    return df


#############
# Section 5 #
#############


def extract_header_s5(content):
    matches = re.search(s5_header_pattern, content)
    if not matches:
        return None
    return [
        "Marker (+)",
        "Marker (?)",
        "Marker (>)",
        f"{matches.group(1)} {matches.group(8)}",
        f"{matches.group(2)} {matches.group(9)}",
        "Marker (*)",
        "Marker (@)",
        f"{matches.group(3)} {matches.group(10)}",
        f"{matches.group(4)} {matches.group(11)}",
        f"{matches.group(5)} {matches.group(12)}",
        f"{matches.group(6)} {matches.group(13)}",
        f"{matches.group(7)} {matches.group(14)}",
    ]


def extract_data_s5(content, header):
    matches = re.findall(s5_data_pattern, content)
    df = pd.DataFrame(matches, columns=header)
    df["Nom du nucléide"] = df["Nom du nucléide"].replace("", np.nan)
    df["LD Energie (mBq/g   )"] = df["LD Energie (mBq/g   )"].replace(
        "Non Calc", np.nan
    )
    df["LD nucléide (mBq/g   )"] = df["LD nucléide (mBq/g   )"].replace("", np.nan)
    df = df.astype(
        {
            "Marker (+)": "bool",
            "Marker (?)": "bool",
            "Marker (>)": "bool",
            "Marker (*)": "bool",
            "Marker (@)": "bool",
        }
    )
    df = df.astype(
        {
            "Energie (keV)": "float64",
            "Intensité (%)": "float64",
            "LD Energie (mBq/g   )": "float64",
            "LD nucléide (mBq/g   )": "float64",
            "Activité (mBq/g   )": "float64",
            "SD Energie (mBq/g   )": "float64",
        }
    )
    df = df.fillna({"Nom du nucléide": df["Nom du nucléide"].ffill()})
    return df


#############
# Section 6 #
#############


def extract_header_s6(content):
    header = []
    matches = re.findall(s6_header_pattern, content)
    l1 = re.findall(s6_word_column_pattern, matches[0][0])
    l2 = re.findall(s6_word_column_pattern, matches[0][1])
    for a, b in zip(reversed(l1), reversed(l2)):
        header.insert(0, f"{a} {b}".strip())
    if len(l1) > len(l2):
        header = l1[: len(l1) - len(l2)] + header
    return header


def extract_data_s6(content, header):
    matches = re.findall(s6_nucleide_line_pattern, content)
    df = pd.DataFrame(matches, columns=header)
    df = df.astype({"Nucléide": "category"})
    df = df.astype(
        {
            "LD": "float64",
            "SD": "float64",
            "Limite Basse": "float64",
            "Limite Haute": "float64",
            "Moyenne Activité": "float64",
            "pondérée Incert.": "float64",
            "Meilleure Activité": "float64",
            "Estimation Incert.": "float64",
        }
    )
    return df


def parse_report(path):
    with open(path, "r") as f:
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


SECTION_DESCRIPTIONS = {
    "s1": "Rapport de l'analyse du spectre (métadonnées)",
    "s2": "Rapport analyse des pics",
    "s3": "Rapport identification des nucléides",
    "s4_nucleides": "Rapport identification avec correction d'interférence — nucléides",
    "s4_pics": "Rapport identification avec correction d'interférence — pics",
    "s5": "Rapport limites de détection",
    "s6": "Rapport limites de détection ISO 11929",
}


def main():
    section_help = "\n".join(f"  {k:<14} {v}" for k, v in SECTION_DESCRIPTIONS.items())
    parser = argparse.ArgumentParser(
        description="Extrait les données structurées d'un rapport Génie200.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"sections disponibles :\n{section_help}\n\nexemples :\n"
        "  %(prog)s rapport.txt\n"
        "  %(prog)s rapport.txt -s s2\n"
        "  %(prog)s rapport.txt -o data/output/",
    )
    parser.add_argument("report", help="chemin vers le rapport Génie200 (.txt)")
    parser.add_argument(
        "--output", "-o", metavar="DIR", help="exporte chaque section en CSV dans DIR"
    )
    parser.add_argument(
        "--section",
        "-s",
        choices=list(SECTION_DESCRIPTIONS),
        metavar="SECTION",
        help="affiche une seule section (voir la liste ci-dessous)",
    )
    args = parser.parse_args()

    data = parse_report(args.report)

    if args.section:
        print(data[args.section].to_string())
        return

    if args.output:
        import os

        os.makedirs(args.output, exist_ok=True)
        for name, df in data.items():
            dest = os.path.join(args.output, f"{name}.csv")
            df.to_csv(dest, index=False)
            print(f"Wrote {dest}")
        return

    for name, df in data.items():
        print(f"\n=== {name} ({len(df)} rows) ===")
        print(df.to_string())


if __name__ == "__main__":
    main()
