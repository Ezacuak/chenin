# ptal-analyse

Parses **Génie 2000 (G2K)** gamma spectrometry reports into pandas DataFrames and CSV exports.

## Sections

| ID | Content |
|----|---------|
| s1 | Report metadata (sample, dates, geometry) |
| s2 | Peak analysis |
| s3 | Nuclide identification |
| s4_nucleides / s4_pics | Identification with interference correction |
| s5 | Detection limits |
| s6 | Detection limits (ISO 11929) |

## Setup

### Intall python

Useing `uv` for windows:

```sh
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

###
Requires Python >= 3.14. With [uv](https://docs.astral.sh/uv/):

```sh
uv sync
```

Or with pip:

```sh
pip install pandas numpy
```

## Usage

```sh
# print all sections
uv run src/poc.py report.txt

# export to CSV
uv run src/poc.py report.txt -o data/output/

# display one section
uv run src/poc.py report.txt -s s3
```

Available sections: `s1`, `s2`, `s3`, `s4_nucleides`, `s4_pics`, `s5`, `s6`.

## Structure

```
ptal-analyse/
├── data/           G2K reports (.txt) and CSV outputs
├── src/
│   ├── poc.py      CLI — extracts all sections from a report
│   └── poc.ipynb   Jupyter notebook for interactive exploration
├── pyproject.toml
└── uv.lock
```
