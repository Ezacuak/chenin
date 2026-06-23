from g2k_parser import Report
from synthesis import SynthesisBuilder


def main():
    reports = []

    for i in range(1, 10):
        reports.append(Report(f"./data/NOI_S/NOI_S_{i}.txt"))

    builder = SynthesisBuilder.from_toml("./data/NOI_S/synthesis.toml")
    synthesis = builder.build(reports)

    print(synthesis.to_string())


if __name__ == "__main__":
    main()
