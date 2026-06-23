import argparse
import os
import sys

from g2k_parser import Report
from synthesis import SynthesisBuilder

SECTION_DESCRIPTIONS = {
    "s1": "Rapport de l'analyse du spectre (métadonnées)",
    "s2": "Rapport analyse des pics",
    "s3": "Rapport identification des nucléides",
    "s4_nucleides": "Rapport identification avec correction d'interférence — nucléides",
    "s4_pics": "Rapport identification avec correction d'interférence — pics",
    "s5": "Rapport limites de détection",
    "s6": "Rapport limites de détection ISO 11929",
}

SUBCOMMANDS = ("extract", "synthesis")


def _add_extract_parser(subparsers):
    section_help = "\n".join(f"  {k:<14} {v}" for k, v in SECTION_DESCRIPTIONS.items())
    p = subparsers.add_parser(
        "extract",
        help="extrait les sections d'un rapport Génie2000",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"sections disponibles :\n{section_help}",
    )
    p.add_argument("report", help="chemin vers le rapport Génie2000 (.txt)")
    p.add_argument(
        "--output", "-o", metavar="DIR", help="exporte chaque section en CSV dans DIR"
    )
    p.add_argument(
        "--section",
        "-s",
        choices=list(SECTION_DESCRIPTIONS),
        metavar="SECTION",
        help="affiche une seule section",
    )
    p.set_defaults(func=_run_extract)


def _add_synthesis_parser(subparsers):
    p = subparsers.add_parser(
        "synthesis",
        help="construit une synthèse multi-rapports à partir d'un fichier TOML",
    )
    p.add_argument("config", help="chemin vers la configuration TOML de synthèse")
    p.add_argument("reports", nargs="+", help="rapports Génie2000 (.txt), dans l'ordre")
    p.add_argument(
        "--output", "-o", metavar="FILE", help="écrit la synthèse en CSV dans FILE"
    )
    p.set_defaults(func=_run_synthesis)


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
    builder = SynthesisBuilder.from_toml(args.config)
    reports = [Report(path) for path in args.reports]
    synthesis = builder.build(reports)

    if args.output:
        synthesis.to_csv(args.output, index=False)
        print(f"Wrote {args.output}")
        return

    print(synthesis.to_string(index=False))


def main():
    parser = argparse.ArgumentParser(
        description="Extrait et synthétise les données des rapports Génie2000.",
    )
    subparsers = parser.add_subparsers(dest="command")
    _add_extract_parser(subparsers)
    _add_synthesis_parser(subparsers)

    # Backward compatibility: `chenin rapport.txt ...` still runs the extractor.
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
