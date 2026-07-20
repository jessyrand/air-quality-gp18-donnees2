import numpy as np
import pandas as pd

NON_NUMERIC_COLUMNS = {"date", "country", "city"}

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

    df = df.dropna(subset=["date"])

    df = df.drop_duplicates()

    df = df.sort_values("date").reset_index(drop=True)

    for col in numeric_cols:
        df.loc[df[col] < 0, col] = np.nan

    df = df.set_index("date")
    df[numeric_cols] = (df[numeric_cols].interpolate(method="time", limit_direction="both").ffill().bfill())
    df = df.reset_index()

    if "country" in df.columns:
        df["country"] = df["country"].ffill().bfill()

    if "city" in df.columns:
        df["city"] = df["city"].ffill().bfill()

    return df