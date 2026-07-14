import numpy as np
import pandas as pd

NON_NUMERIC_COLUMNS = {"date", "country"}

def load_history_csv(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, parse_dates=["date"])
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    return df

def _get_numeric_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in NON_NUMERIC_COLUMNS]
