import pandas as pd
import numpy as np
from ..model.city import City
from .common import HOURLY_VARIABLES, find_city

NON_NUMERIC_COLUMNS = {"date", "country", "city"}

def _build_row(response, cities: list[City]) -> tuple[str, dict]:
    city = find_city(cities, response.Latitude(), response.Longitude())
    city_label = (
        city.name if city is not None else f"{response.Latitude()}_{response.Longitude()}"
    )

    hourly = response.Hourly()

    row = {
        "date": pd.to_datetime(hourly.Time(), unit="s", utc=True),
    }
    for i, variable in enumerate(HOURLY_VARIABLES):
        row[variable] = hourly.Variables(i).ValuesAsNumpy()[0]

    row["country"] = city.country if city is not None else None
    row["city"] = city.name if city is not None else None

    return city_label, row

def clean_last_hourly_row(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    numeric_cols = [c for c in df.columns if c not in NON_NUMERIC_COLUMNS]

    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce")
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    n_before = len(df)
    df = df.dropna(subset=["date"])
    if n_before != len(df):
        print(f"{n_before - len(df)} undated lines deleted)")

    for col in numeric_cols:
        n_negatives = (df[col] < 0).sum()
        if n_negatives > 0:
            print(f"{n_negatives} negative values detected in ‘{col}’ set to NaN")
            df.loc[df[col] < 0, col] = np.nan

    missing = df[numeric_cols].isna().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        print("Missing values detected :")
        print(missing.to_string())

    df = df.drop_duplicates()
    df = df.reset_index(drop=True)

    return df