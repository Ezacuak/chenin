import re

import numpy as np
import pandas as pd

from . import columns as C

###################################################
#                      Regex                      #
###################################################

# Header patterns are no longer used to *derive* column names (those live in
# `columns`). They are kept as layout validators: if a report no longer matches,
# `_require` fails loudly instead of silently mis-aligning the DataFrame.

S1_KV_PATTERN = re.compile(r"^([^:]*):(.*)$", re.MULTILINE)
S2_HEADER_PATTERN = re.compile(
    r"(Numéro)\s+(Début)\s+-\s+(Fin)\s+(Centroïde)\s+(Energie)\s+(FWHM)\s+(Surface)\s+(Incert\.)\s+(Fond sous)\s*\r?\n^\s*(du pic)\s+(\(canaux\))\s+(\(keV\))\s+(\(keV\))\s+(le pic)",
    re.MULTILINE,
)
S2_DATA_PATTERN = re.compile(
    r"^\s*([MmF]?)\s*(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+-\s*(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)",
    re.MULTILINE,
)
S3_HEADER_PATTERN = re.compile(
    r"^\s+(Nom\sdu)\s+(Indice\sde)\s+(Energie)\s+(Intensité)\s+(Activité)\s+(Incert\.)$\n^\s+(nucléide)\s+(confiance)\s+(\W\w+\W)\s+(\W%\W)\s+(\WmBq\Wg\s+\W)\s+(\WmBq\Wg\s+\W)\n",
    re.MULTILINE,
)
S3_DATA_PATTERN = re.compile(
    r"^\s*([A-Z]{1,2}-\d{1,3})?\s*(\d+\.\d+)?\s*(\d+\.\d+)(\*?)\s*(@?)\s*(\d+\.\d+)\s*(?:(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?))?$",
    re.MULTILINE,
)
S4_HEADER_1_PATTERN = re.compile(
    r"^\s*(Nom du)\s+(Indice de)\s+(Activité moyenne)\s+(Incert\.)$\n^\s+(nucléide)\s+(confiance)\s+(pondérée)$\n^\s+(\WmBq\Wg\s+\W)\s+(\WmBq\Wg\s+\W)$",
    re.MULTILINE,
)
S4_HEADER_2_PATTERN = re.compile(
    r"^\s*(Numéro)\s+(Energie)\s+(Intensité)\s+(Incert\.)\s+(Type)\s+(Nucléide)$\n^\s+(du pic)\s+(\WkeV\W)\s+(\Wcoups\Wsec\W)\s+(du pic)\s+(potentiel)$",
    re.MULTILINE,
)
S4_DATA_1_PATTERN = re.compile(
    r"^\s*(X?)\s+([A-Z]{1,2}-\d{1,3})\s*(@?)\s+(\d+\.\d+)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)?\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)?",
    re.MULTILINE,
)
S4_DATA_2_PATTERN = re.compile(
    r"^\s+([MmF])?\s*(\d+)\s+(\d+\.\d+)\s+(\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+(\d+\.\d+)\s*(Sum|D-Esc\.|S-Esc\.|Tol\.)?\s*([A-Z]{1,2}-\d{1,3})?\s*$",
    re.MULTILINE,
)
S5_HEADER_PATTERN = re.compile(
    r"^\s+(Nom\sdu)\s+(Energie)\s+(Intensité)\s*(LD\sEnergie)\s*(LD\snucléide)\s+(Activité)\s+(SD\sEnergie)$\n^\s+(nucléide)\s+(\WkeV\W)\s+(\W%\W)\s+(\WmBq\Wg\s+\W)\s+(\WmBq\Wg\s+\W)\s+(\WmBq\Wg\s+\W)\s+\s+(\WmBq\Wg\s+\W)$",
    re.MULTILINE,
)
S5_DATA_PATTERN = re.compile(
    r"^\s*(\+?)\s*(\??)\s*(>?)\s*([A-Z]{1,2}-\d{1,3})?\s+(\d+\.\d+)(\*?)\s*(@?)\s+(\d+\.\d+)\s+([+\-]?\d+(?:\.\d+)?(?:E[+\-]?\d+)?|Non\sCalc)(?:\s*([+\-]?\d+(?:\.\d+)?(?:E[+\-]?\d+)?))?\s+([+\-]?\d+(?:\.\d+)?(?:E[+\-]?\d+)?)\s+([+\-]?\d+(?:\.\d+)?(?:E[+\-]?\d+)?)$",
    re.MULTILINE,
)
S6_NUCLEIDE_LINE_PATTERN = re.compile(
    r"^[+>?]\s+([A-Z]{1,2}-\d{1,3})\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)",
    re.MULTILINE,
)


def _require(pattern, content, section):
    """Validate that `content` still matches the expected layout for `section`.

    Column names are defined statically in :mod:`columns`; this guard fails
    loudly on a changed report format instead of producing a misaligned frame.
    """
    if not pattern.search(content):
        raise ValueError(
            f"Format de rapport inattendu pour la section {section} : "
            "motif d'en-tete introuvable."
        )


###################################################
#                    Sections                     #
###################################################


#############
# Section 1 #
#############
def extract_s1(content):
    """extract section 1"""
    matches = S1_KV_PATTERN.findall(content)
    return pd.DataFrame(
        {key.strip(): value.strip() for key, value in matches}, index=[0]
    )


#############
# Section 2 #
#############
def extract_s2_header(content):
    """validate section 2 layout and return its column names"""
    _require(S2_HEADER_PATTERN, content, "s2")
    return C.S2_COLS


def extract_s2_data(content, header):
    """extract data of section 2"""
    matches = re.findall(S2_DATA_PATTERN, content)
    df = pd.DataFrame(matches, columns=header)

    df[C.MARKER] = df[C.MARKER].replace("", np.nan)
    df = df.astype({C.MARKER: "category"})
    df = df.astype(
        {
            C.S2_NUMERO: "int64",
            C.S2_DEBUT: "int64",
            C.S2_FIN: "int64",
            C.S2_CENTROIDE: "float64",
            C.ENERGIE_KEV: "float64",
            C.S2_FWHM: "float64",
            C.S2_SURFACE: "float64",
            C.INCERT: "float64",
            C.S2_FOND: "float64",
        }
    )

    return df


#############
# Section 3 #
#############
def extract_s3_header(content):
    """validate section 3 layout and return its column names"""
    _require(S3_HEADER_PATTERN, content, "s3")
    return C.S3_COLS


def extract_s3_data(content, header):
    """extract data of section 3"""
    matches = re.findall(S3_DATA_PATTERN, content)
    df = pd.DataFrame(matches, columns=header)

    df[C.NUCLEIDE] = df[C.NUCLEIDE].replace("", np.nan)
    df[C.INDICE_CONFIANCE] = df[C.INDICE_CONFIANCE].replace("", np.nan)
    df[C.INCERT_MBQ] = df[C.INCERT_MBQ].replace("", np.nan)
    df[C.ACTIVITE_MBQ] = df[C.ACTIVITE_MBQ].replace("", np.nan)

    df = df.astype({C.NUCLEIDE: "category"})
    df = df.astype(
        {
            C.INDICE_CONFIANCE: "float64",
            C.ENERGIE_KEV: "float64",
            C.ACTIVITE_MBQ: "float64",
            C.INCERT_MBQ: "float64",
        }
    )

    df = df.astype({C.S3_MARKER_STAR: "bool", C.S3_MARKER_AT: "bool"})
    df = df.fillna({C.NUCLEIDE: df[C.NUCLEIDE].ffill()})

    return df


#############
# Section 4 #
#############
def extract_s4_nucleides_header(content):
    """validate section 4 (nucleide part) layout and return its column names"""
    _require(S4_HEADER_1_PATTERN, content, "s4_nucleides")
    return C.S4_NUCLEIDES_COLS


def extract_s4_pics_header(content):
    """validate section 4 (pic part) layout and return its column names"""
    _require(S4_HEADER_2_PATTERN, content, "s4_pics")
    return C.S4_PICS_COLS


def extract_s4_nucleides_data(content, header):
    """extract data (nucleide part) of section 4"""
    matches = re.findall(S4_DATA_1_PATTERN, content)
    df = pd.DataFrame(matches, columns=header)
    df = df.astype({C.S4N_MARKER_X: "bool", C.S4N_MARKER_AT: "bool"})
    df[C.S4N_ACTIVITE] = df[C.S4N_ACTIVITE].replace("", np.nan)
    df[C.INCERT_MBQ] = df[C.INCERT_MBQ].replace("", np.nan)
    df = df.astype(
        {
            C.INDICE_CONFIANCE: "object",
            C.S4N_ACTIVITE: "object",
            C.INCERT_MBQ: "object",
            C.NUCLEIDE: "category",
        }
    )
    return df


def extract_s4_pics_data(content, header):
    """extract data (pic part) of section 4"""
    matches = re.findall(S4_DATA_2_PATTERN, content)
    df = pd.DataFrame(matches, columns=header)
    df[C.S4P_MARKER] = df[C.S4P_MARKER].replace("", np.nan)
    df[C.S4P_TYPE] = df[C.S4P_TYPE].replace("", np.nan)
    df[C.S4P_NUCLEIDE] = df[C.S4P_NUCLEIDE].replace("", np.nan)
    df = df.astype(
        {
            C.S4P_MARKER: "category",
            C.S4P_TYPE: "category",
            C.S4P_NUCLEIDE: "category",
        }
    )
    df = df.astype(
        {
            C.S4P_NUMERO: "float64",
            C.ENERGIE_KEV: "float64",
            C.S4P_INTENSITE: "float64",
            C.INCERT: "float64",
        }
    )
    return df


#############
# Section 5 #
#############


def extract_s5_header(content):
    """validate section 5 layout and return its column names"""
    _require(S5_HEADER_PATTERN, content, "s5")
    return C.S5_COLS


def extract_s5_data(content, header):
    """extract data of section 5"""
    matches = re.findall(S5_DATA_PATTERN, content)
    df = pd.DataFrame(matches, columns=header)
    df[C.NUCLEIDE] = df[C.NUCLEIDE].replace("", np.nan)
    df[C.S5_LD_ENERGIE] = df[C.S5_LD_ENERGIE].replace("Non Calc", np.nan)
    df[C.S5_LD_NUCLEIDE] = df[C.S5_LD_NUCLEIDE].replace("", np.nan)
    df = df.astype(
        {
            C.S5_MARKER_PLUS: "bool",
            C.S5_MARKER_Q: "bool",
            C.S5_MARKER_GT: "bool",
            C.S5_MARKER_STAR: "bool",
            C.S5_MARKER_AT: "bool",
        }
    )
    df = df.astype(
        {
            C.ENERGIE_KEV: "float64",
            C.INTENSITE_PCT: "float64",
            C.S5_LD_ENERGIE: "float64",
            C.S5_LD_NUCLEIDE: "float64",
            C.ACTIVITE_MBQ: "float64",
            C.S5_SD_ENERGIE: "float64",
        }
    )
    df = df.fillna({C.NUCLEIDE: df[C.NUCLEIDE].ffill()})
    return df


#############
# Section 6 #
#############


def extract_s6_header(content):
    """validate section 6 layout and return its column names"""
    _require(S6_NUCLEIDE_LINE_PATTERN, content, "s6")
    return C.S6_COLS


def extract_s6_data(content, header):
    """extract data of section 6"""
    matches = re.findall(S6_NUCLEIDE_LINE_PATTERN, content)
    df = pd.DataFrame(matches, columns=header)
    df = df.astype({C.S6_NUCLEIDE: "category"})
    df = df.astype(
        {
            C.S6_LD: "float64",
            C.S6_SD: "float64",
            C.S6_LIMITE_BASSE: "float64",
            C.S6_LIMITE_HAUTE: "float64",
            C.S6_MOYENNE_ACTIVITE: "float64",
            C.S6_PONDEREE_INCERT: "float64",
            C.S6_MEILLEURE_ACTIVITE: "float64",
            C.S6_ESTIMATION_INCERT: "float64",
        }
    )
    return df
