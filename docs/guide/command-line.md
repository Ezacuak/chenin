# Command Line

Everything the app does is available as a command, which is what you want for batch work,
scripting, or a hundred reports you do not care to click through.

```sh
chenin --help
```

Three subcommands: `extract`, `synthesis`, `app`.

## `chenin extract` — one report into tables

```sh
chenin extract data/NOIR24-01/NOI_S_1.txt
```

Prints all seven sections to the terminal, each headed by its name and row count.

```sh
chenin extract data/NOIR24-01/NOI_S_1.txt -s s3
```

Prints one section. Valid keys:

| Key | Content |
|---|---|
| `s1` | Spectrum analysis report (metadata) |
| `s2` | Peak analysis report |
| `s3` | Nuclide identification report |
| `s4_nucleides` | Interference-corrected identification — nuclides |
| `s4_pics` | Interference-corrected identification — peaks |
| `s5` | Detection limits report |
| `s6` | Detection limits report (ISO 11929) |

```sh
chenin extract data/NOIR24-01/NOI_S_1.txt -o out/
```

Writes each section to `out/<section>.csv` and names each file as it goes. The directory is
created if it does not exist. `-s` takes priority over `-o`.

**Shortcut:** `chenin report.txt` means `chenin extract report.txt`. Any first argument
that is not a subcommand is treated as a report path.

| Flag | Default | Meaning |
|---|---|---|
| `--section`, `-s` | all | Print one section only |
| `--output`, `-o` | print | Export every section as CSV into this directory |

## `chenin synthesis` — a folder into one table

```sh
chenin synthesis data/NOIR24-01/ --thickness 0.5
```

Reads every `.txt` in the directory, generates the layer depths, builds the synthesis and
prints it. Unparsable files are skipped with a warning rather than aborting the run.

| Flag | Default | Meaning |
|---|---|---|
| `--start` | `0` | Depth of the first slice, cm |
| `--thickness` | `1` | Slice thickness, cm |
| `--sequential` | off | Stack reports contiguously instead of reading the slice number from the file name |
| `--template`, `-t` | packaged default | Template CSV describing the columns |
| `--output`, `-o` | print | Write the result as CSV to this file |

Worked examples:

```sh
# 0.5 cm slices from the surface, straight to a file
chenin synthesis data/NOIR24-01/ --thickness 0.5 -o NOIR24-01.csv

# core sub-sampled from 12 cm down
chenin synthesis data/NOIR24-01/ --start 12 --thickness 0.5

# reports not numbered by slice: just stack them in order
chenin synthesis data/NOIR24-01/ --sequential --thickness 1

# the lab's own column set
chenin synthesis data/NOIR24-01/ -t templates/lab_2026.csv --thickness 0.5
```

**`--sequential` changes your depths.** By default the slice number comes from the end of
the report name (`NOI_S_13` → 13), which keeps a core with unmeasured slices at its true
depths. `--sequential` ignores the names and stacks reports contiguously, which silently
closes any gap. This matters — see
[Core Layers](https://github.com/Ezacuak/chenin/blob/main/docs/guide/core-layers.md).

**Two limits versus the app.** The CLI applies one uniform slicing rule to the whole core,
so it cannot fix an individual slice that was cut differently. And it has no way to set
`DBD`, so that column comes out empty — which means **a CLI synthesis cannot be exported to
SERAC as-is**. Use the app, or fill the density column afterwards.

## `chenin app` — launch the interface

```sh
chenin app
chenin app --port 8600
```

Serves on `http://localhost:8501` unless `--port` says otherwise, and opens your browser.
`Ctrl+C` in the terminal stops it.

## Scripting it

The output is ordinary CSV, so the usual tools apply:

```sh
# every core in a directory of directories
for core in data/*/; do
    chenin synthesis "$core" --thickness 0.5 -o "out/$(basename "$core").csv"
done
```

For anything more involved, import the package instead — `chenin.Report`,
`chenin.synthesis.SynthesisBuilder` and friends are the same objects the CLI uses. See
[the architecture notes](https://github.com/Ezacuak/chenin/blob/main/docs/dev/architecture.md).
