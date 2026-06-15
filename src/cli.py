import argparse

from parser import parse_report

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
