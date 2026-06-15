# %% [markdown]
# # POC Extraction de données
#
# Extraction des données provenant des rapport de G2K vers un format plus simple.
#
# Import, définition des variables et récupération du contenue du rapport (sous forme de `string`)

# %%
import re
import unicodedata

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# %% [markdown]
# ## Extraction des données de chaque section

# %% [markdown]
# ### Notes
# **TODO**
# - Pour les sections de 2 à 6 extraire les métadonnées.
# - Faire un `ffill` pour les noms de nucléide

# %% [markdown]
# ### Setup
# 1 - On extrait les titre et on créer un dictionnaire de DataFrame
#
# 2- On découpe `content` par section que l'on range dans un dictionnaire `sections_content`

# %% [markdown]
# Définition de mes *regex*

# %%
section_header_pattern = re.compile(r"^\*+$\n^\*{5}(.*)\*{5}$\n^\*+$", re.MULTILINE)
s1_kv_pattern = re.compile(r"^([^:]*):(.*)$", re.MULTILINE)
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


# %%
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


# %%
def strip_accents(s):
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def normalize_columns(df):
    df.columns = [strip_accents(col) for col in df.columns]
    return df


# %% [markdown]
# ### S1 - RAPPORT DE L’ANALYSE DU SPECTRE
# C'est les metadata du rapport.
#
# Pour l'instant ce n'est pas encore bon:
# Mauvaise dections des clés/valeurs


# %%
def section_1(content):
    matches = s1_kv_pattern.findall(content)
    data = pd.DataFrame(
        {key.strip(): value.strip() for key, value in matches}, index=[0]
    )

    return data


# %% [markdown]
# ### S2 - RAPPORT ANALYSE DES PICS


# %%
def extract_header_s2(content):
    match = re.search(s2_header_pattern, content)

    if not match:
        return None

    columns = [
        "Marker",  # Marqueur (M, m, F)
        f"{match.group(1)} {match.group(10)}",  # Numéro du pic
        f"{match.group(2)} {match.group(11)}",  # Début (canaux)
        f"{match.group(3)} {match.group(11)}",  # Fin (canaux)
        match.group(4),  # Centroïde
        f"{match.group(5)} {match.group(12)}",  # Energie (keV)
        f"{match.group(6)} {match.group(13)}",  # FWHM (keV)
        match.group(7),  # Surface
        match.group(8),  # Incert.
        f"{match.group(9)} {match.group(14)}",  # Fond sous le pic
    ]

    return columns


# %%
def extract_data_s2(content, header):
    matches = re.findall(s2_data_pattern, content)
    df = pd.DataFrame(matches, columns=header)

    # Replace all instances of empty string with NaN in column: 'Marker'
    df["Marker"] = df["Marker"].replace("", np.nan)

    # Change column type to category for column: 'Marker'
    df = df.astype({"Marker": "category"})

    # Change column type to float64 for columns: 'Numéro Fond sous', 'Début du pic' and 7 other columns
    df = df.astype(
        {
            "Numéro du pic": "int64",
            "Début (canaux)": "int64",
            "Fin (canaux)": "int64",
            "Centroïde": "float64",
            "Energie (keV)": "float64",
            "FWHM (keV)": "float64",
            "Surface": "float64",
            "Incert.": "float64",
            "Fond sous le pic": "float64",
        }
    )

    return df


# %%
def section_2(content):
    header = extract_header_s2(content)
    data = extract_data_s2(content, header)

    return data


# %% [markdown]
# ### S3 - RAPPORT IDENTIFICATION DES NUCLEIDES


# %%
def extract_header_s3(content):
    matches = re.search(s3_header_pattern, content)

    if not matches:
        return None

    columns = [
        f"{matches.group(1)} {matches.group(7)}",
        f"{matches.group(2)} {matches.group(8)}",
        f"{matches.group(3)} {matches.group(9)}",
        "Marker *",
        "Marker @",
        f"{matches.group(4)} {matches.group(10)}",
        f"{matches.group(5)} {matches.group(11)}",
        f"{matches.group(6)} {matches.group(12)}",
    ]

    return columns


# %%
def extract_data_s3(content, header):
    matches = re.findall(s3_data_pattern, content)
    df = pd.DataFrame(matches, columns=header)

    # Loaded variable 'data_s3' from kernel state

    # Replace all instances of empty string with Nan in columns: 'Nom du nucléide', 'Indice de confiance'
    df["Nom du nucléide"] = df["Nom du nucléide"].replace("", np.nan)
    df["Indice de confiance"] = df["Indice de confiance"].replace("", np.nan)

    # Change column type to float64 for columns: 'Energie (keV)', 'Intensité (%)' and 3 other columns
    df = df.astype(
        {
            "Energie (keV)": "float64",
            "Intensité (%)": "float64",
            "Activité (mBq/g   )": "float64",
            "Incert. (mBq/g   )": "float64",
            "Indice de confiance": "float64",
        }
    )

    # Replace gaps forward from the previous valid value in: 'Nom du nucléide'
    df = df.fillna({"Nom du nucléide": df["Nom du nucléide"].ffill()})

    # Change column type to category for column: 'Nom du nucléide'
    df = df.astype({"Nom du nucléide": "category"})

    # Change column type to bool for columns: 'Marker *', 'Marker @'
    df = df.astype({"Marker *": "bool", "Marker @": "bool"})

    return df


# %%
def section_3(content):
    header = extract_header_s3(content)
    data = extract_data_s3(content, header)

    return data


# %% [markdown]
# ### S4 - RAPPORT IDENTIFICATION AVEC CORRECTION D’INTERFERENCE


# %%
def extract_header_1_s4(content):
    matches = re.search(s4_header_1_pattern, content)
    if not matches:
        return None

    columns = [
        "Marker (X)",
        f"{matches.group(1)} {matches.group(5)}",
        "Marker (@)",
        f"{matches.group(2)} {matches.group(6)}",
        f"{matches.group(3)} {matches.group(7)} {matches.group(8)}",
        f"{matches.group(4)} {matches.group(9)}",
    ]

    return columns


# %%
def extract_header_2_s4(content):
    matches = re.search(s4_header_2_pattern, content)

    if not matches:
        return None

    columns = [
        "Marker (M/m/F)",
        f"{matches.group(1)} {matches.group(7)}",
        f"{matches.group(2)} {matches.group(8)}",
        f"{matches.group(3)} {matches.group(9)}",
        f"{matches.group(4)}",
        f"{matches.group(5)} {matches.group(10)}",
        f"{matches.group(6)} {matches.group(11)}",
    ]

    return columns


# %%
def extract_data_1_s4(content, header):
    matches = re.findall(s4_data_1_pattern, content)
    df = pd.DataFrame(matches, columns=header)

    # Change column type to bool for columns: 'Marker (X)', 'Marker (@)'
    df = df.astype({"Marker (X)": "bool", "Marker (@)": "bool"})

    # Replace all instances of empty string with NaN in columns: 'Activité moyenne pondérée (mBq/g   )', 'Incert. (mBq/g   )'
    df["Activité moyenne pondérée (mBq/g   )"] = df[
        "Activité moyenne pondérée (mBq/g   )"
    ].replace("", np.nan)
    df["Incert. (mBq/g   )"] = df["Incert. (mBq/g   )"].replace("", np.nan)

    # Change column type to object for columns: 'Indice de confiance', 'Activité moyenne pondérée (mBq/g   )', 'Incert. (mBq/g   )'
    df = df.astype(
        {
            "Indice de confiance": "float64",
            "Activité moyenne pondérée (mBq/g   )": "float64",
            "Incert. (mBq/g   )": "float64",
        }
    )

    # Change column type to category for column: 'Nom du nucléide'
    df = df.astype({"Nom du nucléide": "category"})

    return df


# %%
def extract_data_2_s4(content, header):
    matches = re.findall(s4_data_2_pattern, content)
    df = pd.DataFrame(matches, columns=header)

    # Replace all instances of empty string with NaN in columns: 'Marker (M/m/F)', 'Type du pic', 'Nucléide potentiel'
    df["Marker (M/m/F)"] = df["Marker (M/m/F)"].replace("", np.nan)
    df["Type du pic"] = df["Type du pic"].replace("", np.nan)
    df["Nucléide potentiel"] = df["Nucléide potentiel"].replace("", np.nan)

    # Change column type to category for columns: 'Marker (M/m/F)', 'Type du pic', 'Nucléide potentiel'
    df = df.astype(
        {
            "Marker (M/m/F)": "category",
            "Type du pic": "category",
            "Nucléide potentiel": "category",
        }
    )

    # Change column type to float64 for columns: 'Numéro du pic', 'Energie (keV)' and 2 other columns
    df = df.astype(
        {
            "Numéro du pic": "float64",
            "Energie (keV)": "float64",
            "Intensité (coups/sec)": "float64",
            "Incert.": "float64",
        }
    )

    return df


# %%
def section_4_p1(content):
    header = extract_header_1_s4(content)
    data = extract_data_1_s4(content, header)

    return data


def section_4_p2(content):
    header = extract_header_2_s4(content)
    data = extract_data_2_s4(content, header)

    return data


# %% [markdown]
# ### S5 - RAPPORT LIMITES DE DETECTION


# %%
def extract_header_s5(content):
    matches = re.search(s5_header_pattern, content)

    if not matches:
        return None

    columns = [
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

    return columns


# %%
def extract_data_s5(content, header):
    matches = re.findall(s5_data_pattern, content)
    df = pd.DataFrame(matches, columns=header)

    # Loaded variable 'data_s5' from kernel state

    # Replace all instances of empty string with NaN in column: 'Nom du nucléide'
    df["Nom du nucléide"] = df["Nom du nucléide"].replace("", np.nan)

    # Replace all instances of 'Non Calc' with NaN in column: 'LD Energie (mBq/g   )'
    df["LD Energie (mBq/g   )"] = df["LD Energie (mBq/g   )"].replace(
        "Non Calc", np.nan
    )

    # Replace all instances of empty string with NaN in column: 'LD nucléide (mBq/g   )'
    df["LD nucléide (mBq/g   )"] = df["LD nucléide (mBq/g   )"].replace("", np.nan)

    # Change column type to bool for columns: 'Marker (+)', 'Marker (?)' and 3 other columns
    df = df.astype(
        {
            "Marker (+)": "bool",
            "Marker (?)": "bool",
            "Marker (>)": "bool",
            "Marker (*)": "bool",
            "Marker (@)": "bool",
        }
    )

    # Change column type to float64 for columns: 'Energie (keV)', 'Intensité (%)' and 4 other columns
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

    # Replace gaps forward from the previous valid value in: 'Nom du nucléide'
    df = df.fillna({"Nom du nucléide": df["Nom du nucléide"].ffill()})

    return df


# %%
def section_5(content):
    header = extract_header_s5(content)
    data = extract_data_s5(content, header)

    return data


# %% [markdown]
# ### S6 - RAPPORT LIMITES DE DETECTION  ISO 11929


# %%
def extract_header_s6(content):
    header = []
    matches = re.findall(s6_header_pattern, content)

    l1 = re.findall(s6_word_column_pattern, matches[0][0])
    l2 = re.findall(s6_word_column_pattern, matches[0][1])

    # Fusion en partant de la fin
    for a, b in zip(reversed(l1), reversed(l2)):
        header.insert(0, f"{a} {b}".strip())

    # Si l1 est plus longue, on conserve le début restant
    if len(l1) > len(l2):
        header = l1[: len(l1) - len(l2)] + header

    return header


# %%
def extract_data_s6(content, header):
    matches = re.findall(s6_nucleide_line_pattern, content)
    df = pd.DataFrame(matches, columns=header)

    # Change column type to category for column: 'Nucléide'
    df = df.astype({"Nucléide": "category"})

    # Change column type to float64 for columns: 'LD', 'SD' and 6 other columns
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


# %%
def section_6(content):
    header = extract_header_s6(content)
    data = extract_data_s6(content, header)

    return data


# %% [markdown]
# ### Extraction rapport


# %%
def report(file: str) -> dict:
    with open(file, "r") as f:
        content = f.read()

    titles, sections = split_sections(content)

    return {
        "s1": normalize_columns(section_1(sections[titles[0]])),
        "s2": normalize_columns(section_2(sections[titles[1]])),
        "s3": normalize_columns(section_3(sections[titles[2]])),
        "s4_nucleides": normalize_columns(section_4_p1(sections[titles[3]])),
        "s4_pics": normalize_columns(section_4_p2(sections[titles[3]])),
        "s5": normalize_columns(section_5(sections[titles[4]])),
        "s6": normalize_columns(section_6(sections[titles[5]])),
    }


# %% [markdown]
# ## Vérification des données

# %% [markdown]
# ### Qualité de l'extraction
# Je verifie que les donnée que j'extrait corresponde réelement au données du fichier `.txt`

# %%
# FIXME: Section 1 Done
# FIXME: Section 2 Done
# FIXME: Section 3 Done
# FIXME: Section 4_1 Don
# FIXME: Section 4_2 Done
# FIXME: Section 5
# FIXME: Section 6

ech = 16
section = 5

df = report(f"../data/NOI_S/NOI_S_{ech}.txt")["s5"]
# for i in [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 16]:
# df = pd.concat([df, report(f"../data/NOI_S/NOI_S_{i}.txt")[f"s{section}"]], ignore_index=True)

df


# %% [markdown]
# ### Qualité des donneés
# Chargement des données et petit netoyage
#
# `cv_*` -> "certified values"\
# `nc_*` -> "non certified values"

# %%
cv_rgth = pd.read_csv("../data/test/ceritfied_values-RGTh.csv")
cv_rgth = cv_rgth.astype({"Nucleide": "category"})

nc_rgth = report("../data/test/rapport-RGTh_3cm.txt")


cv_rgu = pd.read_csv("../data/test/ceritfied_values-RGU.csv")
cv_rgu = cv_rgu.astype({"Nucleide": "category"})

nc_rgu = report("../data/test/rapport-RGU_3cm.txt")

cv_s447 = pd.read_csv("../data/test/ceritfied_values-S447.csv")
cv_s447 = cv_s447.astype({"Nucleide": "category"})

nc_s447 = report("../data/test/rapport-S447_3cm.txt")

# %% [markdown]
# #### Comparaison des données (Rapport/Ceritifée)
# On a seulement besoin de la section 6 des rapports

# %% [markdown]
# Pour `RGTh`.
#
# Premiere etape: Faire les equivalence d'equilibre entre isotope.
#
# Par exemple le `TH-232` est à l'equilibre avec le `PB-212` et `TH-228`
#

# %%


# %%
s6 = nc_rgth["s6"]
data = s6[["Nucleide", "Moyenne Activite"]]

fig = px.bar(
    data,
    x="Nucleide",
    y="Moyenne Activite",
    title="Activitée moyenne par nucléides dans RGTh",
)
fig.show()

# %% [markdown]
# Avec les incertitudes

# %%

s6 = nc_rgth["s6"]
data = s6[["Nucleide", "Moyenne Activite"]]


fig = go.Figure(
    data=go.Bar(
        x=s6["Nucleide"],
        y=s6["Moyenne Activite"],
        error_y=dict(
            type="data",
            array=s6["Estimation Incert."],
            symmetric=True,  # Désactive la symétrie pour contrôler le haut/bas
            # arrayminus=[0]*len(s6),   # Force l'incertitude vers le bas à 0
            visible=True,
            color="black",  # Couleur de la barre d'erreur
            thickness=2,  # Épaisseur de la ligne
            width=6,  # Largeur des petits tirets horizontaux aux extrémités
        ),
    )
)

fig.show()

# %% [markdown]
# ## Zone de Test

# %%
noi_s_1 = report("../data/NOI_S/NOI_S_1.txt")

print(noi_s_1["s3"].columns)

# %%
noi_s_1["s4_nucleides"].columns
