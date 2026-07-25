from pathlib import Path

import pandas as pd

from .model.city import CITIES
from .transform.build_warehouse import build_warehouse

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CLEAN_FILE = DATA_DIR / "clean" / "clean.csv"


def main():
    if not CLEAN_FILE.exists():
        raise FileNotFoundError(
            f"{CLEAN_FILE} not found. Run fetch_history and build_clean first."
        )

    clean_df = pd.read_csv(
        CLEAN_FILE,
        parse_dates=["date"],
    )

    build_warehouse(
        clean_df=clean_df,
        cities=CITIES,
        full_refresh=True,
    )


if __name__ == "__main__":
    main()