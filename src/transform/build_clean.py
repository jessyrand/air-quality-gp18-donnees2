from pathlib import Path

import pandas as pd

from .merge_history import clean_dataframe, load_history_csv

DATA_DIR = Path(__file__).parent.parent / "data"

RAW_DIR = DATA_DIR / "raw"
CLEAN_DIR = DATA_DIR / "clean"


def rebuild_clean() -> pd.DataFrame:
    """
    Rebuild clean.csv from every raw file.

    The clean dataset is fully reconstructed at each execution.
    """

    history_files = sorted((RAW_DIR / "history").glob("*.csv"))
    hourly_files = sorted((RAW_DIR / "hourly").glob("*.csv"))

    print(f"[clean] History files : {len(history_files)}")
    print(f"[clean] Hourly files : {len(hourly_files)}")

    frames = []

    #
    # History
    #

    for file in history_files:

        df = load_history_csv(file)

        city = (
            file.stem
            .replace("_history", "")
            .replace("_", " ")
            .title()
        )

        if "city" not in df.columns:
            df["city"] = city

        df = clean_dataframe(df)

        frames.append(df)

    #
    # Hourly
    #

    for file in hourly_files:

        df = load_history_csv(file)

        df = clean_dataframe(df)

        frames.append(df)

    if not frames:
        raise ValueError("No raw data found.")

    clean = pd.concat(frames, ignore_index=True)

    required_columns = {"date", "city", "country"}

    missing = required_columns - set(clean.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing))}"
        )

    clean = clean.drop_duplicates(
        subset=["city", "date"],
        keep="last",
    )

    clean = clean.sort_values(
        ["date", "city"]
    ).reset_index(drop=True)

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    output_file = CLEAN_DIR / "clean.csv"

    clean.to_csv(
        output_file,
        index=False,
    )

    print(f"[clean] {len(clean)} rows written to {output_file}")

    return clean

def main():
    rebuild_clean()


if __name__ == "__main__":
    main()