import numpy as np
import pandas as pd

NON_NUMERIC_COLUMNS = {"date", "country"}

def load_history_csv(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, parse_dates=["date"])
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    return df

def _get_numeric_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in NON_NUMERIC_COLUMNS]

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    numeric_cols = _get_numeric_columns(df)

    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    n_before = len(df)
    df = df.dropna(subset=["date"])
    if n_before != len(df):
        print(f"{n_before - len(df)} lines without dates deleteds")

    n_before = len(df)
    df = df.drop_duplicates()
    if n_before != len(df):
        print(f"{n_before - len(df)} duplicates removed")

    df = df.sort_values("date").reset_index(drop=True)

    missing_before = df[numeric_cols].isna().sum()
    missing_before = missing_before[missing_before > 0]
    if not missing_before.empty:
        print("Missing values before processing:")
        print(missing_before.to_string())

    df = df.set_index("date")
    df[numeric_cols] = df[numeric_cols].interpolate(method="time", limit_direction="both")
    df = df.reset_index()

    df[numeric_cols] = df[numeric_cols].ffill().bfill()

    if "country" in df.columns and df["country"].isna().any():
        df["country"] = df["country"].ffill().bfill()

    return df