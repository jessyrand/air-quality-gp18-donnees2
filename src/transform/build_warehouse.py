import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from ..extract.common import HOURLY_VARIABLES
from ..model.city import City

load_dotenv()

MEASURE_COLUMNS = HOURLY_VARIABLES
OUTPUT_DIR = Path("warehouse")


def build_dim_city(cities: list[City]) -> pd.DataFrame:
    rows = [
        {
            "city_name": c.name,
            "country": c.country,
            "latitude": c.latitude,
            "longitude": c.longitude,
        }
        for c in cities
    ]

    dim_city = pd.DataFrame(rows)
    dim_city.insert(0, "city_id", range(1, len(dim_city) + 1))
    return dim_city


def build_dim_time(clean_df: pd.DataFrame) -> pd.DataFrame:
    unique_dates = pd.to_datetime(clean_df["date"].dropna().unique())
    unique_dates = pd.Series(unique_dates).sort_values().reset_index(drop=True)

    dim_time = pd.DataFrame({"full_datetime": unique_dates})
    dim_time.insert(0, "time_id", range(1, len(dim_time) + 1))
    dim_time["date"] = dim_time["full_datetime"].dt.date
    dim_time["hour"] = dim_time["full_datetime"].dt.hour
    dim_time["day_of_week"] = dim_time["full_datetime"].dt.day_name()
    dim_time["is_weekend"] = dim_time["full_datetime"].dt.weekday >= 5
    dim_time["month"] = dim_time["full_datetime"].dt.month
    dim_time["year"] = dim_time["full_datetime"].dt.year

    return dim_time


def build_fact_aqi(clean_df: pd.DataFrame, dim_city: pd.DataFrame, dim_time: pd.DataFrame) -> pd.DataFrame:
    fact = clean_df.merge(
        dim_city[["city_id", "city_name"]],
        left_on="city",
        right_on="city_name",
        how="left",
    )
    fact = fact.merge(
        dim_time[["time_id", "full_datetime"]],
        left_on="date",
        right_on="full_datetime",
        how="left",
    )

    measure_cols = [c for c in MEASURE_COLUMNS if c in fact.columns]

    if not measure_cols:
        print("[warehouse] WARNING: no measure column found, check HOURLY_VARIABLES in common.py")

    fact = fact[["city_id", "time_id"] + measure_cols].copy()
    fact.insert(0, "fact_id", range(1, len(fact) + 1))

    missing_city = int(fact["city_id"].isna().sum())
    missing_time = int(fact["time_id"].isna().sum())
    if missing_city or missing_time:
        print(f"[warehouse] WARNING: {missing_city} rows with no city_id, {missing_time} rows with no time_id")

    return fact


def check_coherence(fact: pd.DataFrame, dim_city: pd.DataFrame, dim_time: pd.DataFrame) -> None:
    n_cities = dim_city["city_id"].nunique()
    n_hours = dim_time["time_id"].nunique()
    expected = n_cities * n_hours
    actual = len(fact)

    print(f"[warehouse] cities = {n_cities}, hours covered = {n_hours}")
    print(f"[warehouse] expected rows ~= {expected}, actual rows = {actual} (gap = {expected - actual})")

    coverage = fact.groupby("city_id")["time_id"].nunique()
    for city_id, count in coverage.items():
        if count != n_hours:
            city_name = dim_city.loc[dim_city["city_id"] == city_id, "city_name"].iloc[0]
            print(f"[warehouse]   -> {city_name}: {count}/{n_hours} hours covered")


def export_warehouse(
    dim_city: pd.DataFrame,
    dim_time: pd.DataFrame,
    fact: pd.DataFrame,
    output_dir: Path = OUTPUT_DIR,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    dim_city.to_csv(output_dir / "dim_city.csv", index=False)
    dim_time.to_csv(output_dir / "dim_time.csv", index=False)
    fact.to_csv(output_dir / "fact_aqi.csv", index=False)
    print(f"[warehouse] files exported to {output_dir}/")


def get_engine():
    from sqlalchemy import create_engine

    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER", "aqi_user")
    password = os.environ.get("POSTGRES_PASSWORD", "aqi_password")
    db = os.environ.get("POSTGRES_DB", "aqi_warehouse")
    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    return create_engine(url)


def load_to_postgres(dim_city: pd.DataFrame, dim_time: pd.DataFrame, fact: pd.DataFrame, engine=None) -> None:
    from sqlalchemy import text

    engine = engine or get_engine()

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE fact_aqi, dim_time, dim_city RESTART IDENTITY CASCADE"))

    dim_city.to_sql("dim_city", engine, if_exists="append", index=False)
    dim_time.to_sql("dim_time", engine, if_exists="append", index=False)
    fact.to_sql("fact_aqi", engine, if_exists="append", index=False)

    with engine.begin() as conn:
        for table, pk in [("dim_city", "city_id"), ("dim_time", "time_id"), ("fact_aqi", "fact_id")]:
            conn.execute(text(
                f"SELECT setval(pg_get_serial_sequence('{table}', '{pk}'), COALESCE(MAX({pk}), 1)) FROM {table}"
            ))

    print(f"[warehouse] {len(dim_city)} cities, {len(dim_time)} timestamps, {len(fact)} facts loaded into Postgres")


def build_warehouse(
    clean_df: pd.DataFrame,
    cities: list[City],
    to_postgres: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    dim_city = build_dim_city(cities)
    dim_time = build_dim_time(clean_df)
    fact = build_fact_aqi(clean_df, dim_city, dim_time)

    check_coherence(fact, dim_city, dim_time)
    export_warehouse(dim_city, dim_time, fact)
    if to_postgres:
        load_to_postgres(dim_city, dim_time, fact)
    return dim_city, dim_time, fact
