import sys
from pathlib import Path

import streamlit.web.cli as stcli

from synthesis import BuildConfig, SynthesisBuilder, load_reports


def main():
    build_file = "./NOI_S_Builder.toml"
    config = BuildConfig.from_toml(build_file)
    reports = load_reports(config, Path(build_file).parent)
    synthesis = SynthesisBuilder(config).build(reports)

    print(synthesis.to_string())


def streamlit():
    sys.argv = ["streamlit", "run", "src/app.py"]
    sys.exit(stcli.main())


if __name__ == "__main__":
    # main()
    streamlit()
