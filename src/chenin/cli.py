import argparse
import os
import sys
from pathlib import Path

from chenin.g2k_parser import SECTION_DESCRIPTIONS, Report
from chenin.synthesis import BuildConfig, SynthesisBuilder, load_reports

SUBCOMMANDS = ("extract", "synthesis", "app")


def _add_extract_parser(subparsers):
    section_help = "\n".join(f"  {k:<14} {v}" for k, v in SECTION_DESCRIPTIONS.items())
    p = subparsers.add_parser(
        "extract",
        help="extract the sections of a Génie 2000 report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"available sections:\n{section_help}",
    )
    p.add_argument("report", help="path to the Génie 2000 report (.txt)")
    p.add_argument("--output", "-o", metavar="DIR", help="export each section as CSV into DIR")
    p.add_argument(
        "--section",
        "-s",
        choices=list(SECTION_DESCRIPTIONS),
        metavar="SECTION",
        help="print a single section",
    )
    p.set_defaults(func=_run_extract)


def _add_synthesis_parser(subparsers):
    p = subparsers.add_parser(
        "synthesis",
        help="build a synthesis from a roadmap file",
    )
    p.add_argument(
        "roadmap",
        help="path to the roadmap file (sample list, CSV or Excel)",
    )
    p.add_argument(
        "--template",
        "-t",
        metavar="FILE",
        help="synthesis template CSV (defaults to the packaged lab template)",
    )
    p.add_argument("--output", "-o", metavar="FILE", help="write the synthesis as CSV to FILE")
    p.set_defaults(func=_run_synthesis)


def _add_app_parser(subparsers):
    p = subparsers.add_parser("app", help="launch the Chenin Streamlit app")
    p.add_argument(
        "--port", type=int, default=8501, help="port to serve the app on (default: 8501)"
    )
    p.set_defaults(func=_run_app)


def _run_extract(args):
    data = Report(args.report)

    if args.section:
        print(data[args.section].to_string())
        return

    if args.output:
        os.makedirs(args.output, exist_ok=True)
        for name, df in data.items():
            dest = os.path.join(args.output, f"{name}.csv")
            df.to_csv(dest, index=False)
            print(f"Wrote {dest}")
        return

    for name, df in data.items():
        print(f"\n=== {name} ({len(df)} rows) ===")
        print(df.to_string())


def _run_synthesis(args):
    config = BuildConfig.from_roadmap(args.roadmap, args.template)
    reports = load_reports(config, Path(args.roadmap).parent)
    synthesis = SynthesisBuilder(config).build(reports)

    if args.output:
        synthesis.to_csv(args.output, index=False)
        print(f"Wrote {args.output}")
        return

    print(synthesis.to_string(index=False))


def _run_app(args):
    import streamlit.web.cli as stcli

    app_path = Path(__file__).parent / "ui" / "app.py"
    sys.argv = ["streamlit", "run", str(app_path), "--server.port", str(args.port)]
    sys.exit(stcli.main())


def main():
    parser = argparse.ArgumentParser(
        description="Extract and synthesise data from Génie 2000 reports.",
    )
    subparsers = parser.add_subparsers(dest="command")
    _add_extract_parser(subparsers)
    _add_synthesis_parser(subparsers)
    _add_app_parser(subparsers)

    # Backward compatibility: `chenin report.txt ...` still runs the extractor.
    argv = sys.argv[1:]
    if argv and argv[0] not in SUBCOMMANDS and argv[0] not in ("-h", "--help"):
        argv = ["extract", *argv]

    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
