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
        print(f"{n_before - len(df)} undated lines deleted")

    n_before = len(df)
    df = df.drop_duplicates()
    if n_before != len(df):
        print(f"{n_before - len(df)} duplicates removed")

    df = df.sort_values("date").reset_index(drop=True)

    for col in numeric_cols:
        n_negatives = (df[col] < 0).sum()
        if n_negatives > 0:
            print(f"{n_negatives} negative values detected in ‘{col}’ set to NaN")
            df.loc[df[col] < 0, col] = np.nan

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

def merge_history_dataframe(old_df: pd.DataFrame,new_df: pd.DataFrame,) -> pd.DataFrame:
    old_df = clean_dataframe(old_df)
    new_df = clean_dataframe(new_df)

    merged_df = pd.concat([old_df, new_df], ignore_index=True)
    merged_df = merged_df.drop_duplicates(subset=["date"], keep="last")
    merged_df = merged_df.sort_values("date")
    merged_df = merged_df.reset_index(drop=True)

    return merged_df