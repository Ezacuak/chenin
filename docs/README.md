# Chenin documentation

## User guide

These pages are also rendered inside the app, under **Documentation** in the sidebar. The
markdown files here are the source — there is no second copy to drift out of date.

| Page | Read it for |
|---|---|
| [Overview](guide/overview.md) | What Chenin does, the workflow, the vocabulary |
| [Install & Update](guide/install.md) | Getting it running, including a first terminal |
| [Loading Reports](guide/loading-reports.md) | Uploading `.txt` reports, the seven sections, browsing and filtering |
| [Core Layers](guide/core-layers.md) | Report selection, the nuclide library, depths and the slice-numbering rule |
| [Building Columns](guide/building-columns.md) | The five competing column-builder designs |
| [Templates](guide/synthesis-template.md) | The two-row template CSV |
| [Formulas](guide/formulas.md) | Derived columns, syntax, uncertainty propagation |
| [Formula Tester](guide/formula-tester.md) | The live scratchpad (in-app page) |
| [Exporting](guide/exporting.md) | CSV, Parquet and SERAC output |
| [Command Line](guide/command-line.md) | `extract`, `synthesis`, `app` and their flags |
| [Troubleshooting](guide/troubleshooting.md) | When something goes wrong |

## Developer guide

Repo-only — these are not shipped in the wheel and not shown in the app.

| Page | Read it for |
|---|---|
| [Architecture](dev/architecture.md) | Package layout, the two data flows, the validation contract |
| [Parsing G2K reports](dev/parsing-g2k.md) | How a report becomes DataFrames, and how to change that |
| [Contributing](dev/contributing.md) | uv, tests, lint, and how to add things |
| [Deploy](dev/deploy.md) | Lab machines, Docker, cutting a release |
| [Known issues](dev/known-issues.md) | Confirmed rough edges, with reproductions |
