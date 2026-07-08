"""Single source of truth for G2K report column names.

Names are stored **already accent-stripped (ASCII)** and with the unit padding
cleaned (``(mBq/g   )`` -> ``(mBq/g)``), i.e. exactly as they appear in the
parsed DataFrames. Both the parser (:mod:`g2k_parser._sections`) and downstream
consumers (e.g. :mod:`synthesis`) import from here, so the schema is defined in
exactly one place.

Accents are normalized *here*, ahead of any data processing -- this is what
lets the extraction code reference columns by stable ASCII keys (and is why the
old "strip accents at the very end" approach kept breaking with ``KeyError``).
"""

# --- shared columns --------------------------------------------------------
MARKER = "Marker"
NUCLEIDE = "Nom du nucleide"  # s3, s4_nucleides, s5
ENERGIE_KEV = "Energie (keV)"  # s2, s3, s4_pics, s5
INDICE_CONFIANCE = "Indice de confiance"
INTENSITE_PCT = "Intensite (%)"
ACTIVITE_MBQ = "Activite (mBq/g)"  # s3, s5
INCERT_MBQ = "Incert. (mBq/g)"  # s3, s4_nucleides
INCERT = "Incert."  # s2, s4_pics

# --- section 2: peak analysis ---------------------------------------------
S2_NUMERO = "Numero du pic"
S2_DEBUT = "Debut (canaux)"
S2_FIN = "Fin (canaux)"
S2_CENTROIDE = "Centroide"
S2_FWHM = "FWHM (keV)"
S2_SURFACE = "Surface"
S2_FOND = "Fond sous le pic"
S2_COLS = [
    MARKER,
    S2_NUMERO,
    S2_DEBUT,
    S2_FIN,
    S2_CENTROIDE,
    ENERGIE_KEV,
    S2_FWHM,
    S2_SURFACE,
    INCERT,
    S2_FOND,
]

# --- section 3: nuclide identification ------------------------------------
S3_MARKER_STAR = "Marker *"
S3_MARKER_AT = "Marker @"
S3_COLS = [
    NUCLEIDE,
    INDICE_CONFIANCE,
    ENERGIE_KEV,
    S3_MARKER_STAR,
    S3_MARKER_AT,
    INTENSITE_PCT,
    ACTIVITE_MBQ,
    INCERT_MBQ,
]

# --- section 4: identification with interference correction ---------------
# nucleides sub-table
S4N_MARKER_X = "Marker (X)"
S4N_MARKER_AT = "Marker (@)"
S4N_ACTIVITE = "Activite moyenne ponderee (mBq/g)"
S4_NUCLEIDES_COLS = [
    S4N_MARKER_X,
    NUCLEIDE,
    S4N_MARKER_AT,
    INDICE_CONFIANCE,
    S4N_ACTIVITE,
    INCERT_MBQ,
]
# pics sub-table
S4P_MARKER = "Marker (M/m/F)"
S4P_NUMERO = "Numero du pic"
S4P_INTENSITE = "Intensite (coups/sec)"
S4P_TYPE = "Type du pic"
S4P_NUCLEIDE = "Nucleide potentiel"
S4_PICS_COLS = [
    S4P_MARKER,
    S4P_NUMERO,
    ENERGIE_KEV,
    S4P_INTENSITE,
    INCERT,
    S4P_TYPE,
    S4P_NUCLEIDE,
]

# --- section 5: detection limits ------------------------------------------
S5_MARKER_PLUS = "Marker (+)"
S5_MARKER_Q = "Marker (?)"
S5_MARKER_GT = "Marker (>)"
S5_MARKER_STAR = "Marker (*)"
S5_MARKER_AT = "Marker (@)"
S5_LD_ENERGIE = "LD Energie (mBq/g)"
S5_LD_NUCLEIDE = "LD nucleide (mBq/g)"
S5_SD_ENERGIE = "SD Energie (mBq/g)"
S5_COLS = [
    S5_MARKER_PLUS,
    S5_MARKER_Q,
    S5_MARKER_GT,
    NUCLEIDE,
    ENERGIE_KEV,
    S5_MARKER_STAR,
    S5_MARKER_AT,
    INTENSITE_PCT,
    S5_LD_ENERGIE,
    S5_LD_NUCLEIDE,
    ACTIVITE_MBQ,
    S5_SD_ENERGIE,
]

# --- section 6: detection limits (ISO 11929) ------------------------------
S6_NUCLEIDE = "Nucleide"
S6_LD = "LD"
S6_SD = "SD"
S6_LIMITE_BASSE = "Limite Basse"
S6_LIMITE_HAUTE = "Limite Haute"
S6_MOYENNE_ACTIVITE = "Moyenne Activite"
S6_INCERT_PONDEREE = "ponderee Incert."
S6_MEILLEURE_ACTIVITE = "Meilleure Activite"
S6_ESTIMATION_INCERT = "Estimation Incert."
S6_COLS = [
    S6_NUCLEIDE,
    S6_LD,
    S6_SD,
    S6_LIMITE_BASSE,
    S6_LIMITE_HAUTE,
    S6_MOYENNE_ACTIVITE,
    S6_INCERT_PONDEREE,
    S6_MEILLEURE_ACTIVITE,
    S6_ESTIMATION_INCERT,
]
