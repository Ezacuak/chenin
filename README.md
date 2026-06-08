# ptal-analyse

Parses **Génie 2000 (G2K)** gamma spectrometry reports into pandas DataFrames and CSV exports. Built for EDYTEM-PTAL research.

## Sections

| ID | Content |
|----|---------|
| s1 | Report metadata (sample, dates, geometry) |
| s2 | Peak analysis |
| s3 | Nuclide identification |
| s4_nucleides / s4_pics | Identification with interference correction |
| s5 | Detection limits |
| s6 | Detection limits (ISO 11929) |

## Installation

### Option 1: Development (local)

Requires Python >= 3.14 and [uv](https://docs.astral.sh/uv/):

```sh
# Clone the repository
git clone <repo-url>
cd ptal-analyse

# Install dependencies
uv sync

# Run the CLI
uv run src/poc.py report.txt
```

### Option 2: Global tool installation

Install as a global command available anywhere on your system:

```sh
# From git repository
uv tool install git+https://codeberg.org/Ezacuak/ptal-analyse

# Then use directly
ptal-analyse report.txt
ptal-analyse report.txt -o output/
```

## Usage

```sh
# Print all sections to stdout
ptal-analyse report.txt

# Export to CSV
ptal-analyse report.txt -o data/output/

# Display one section
ptal-analyse report.txt -s s3
```

**Available sections**: `s1`, `s2`, `s3`, `s4_nucleides`, `s4_pics`, `s5`, `s6`.

### Interactive exploration

For prototyping and analysis, launch Jupyter:

```sh
uv run jupyter lab
```

Then open [src/poc.ipynb](src/poc.ipynb) for interactive extraction and testing.

## Project Structure

```
ptal-analyse/
├── data/           G2K reports (.txt) and CSV outputs
├── src/
│   ├── poc.py      CLI and extraction logic
│   └── poc.ipynb   Jupyter notebook for exploration
├── CLAUDE.md       Architecture and design notes
├── pyproject.toml
└── uv.lock
```

## Development

Lint with ruff:

```sh
uvx ruff check src/
```

No test suite configured yet.
