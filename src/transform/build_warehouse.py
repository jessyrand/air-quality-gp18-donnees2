import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from ..extract.common import HOURLY_VARIABLES
from ..model.city import City
from ..model.city import CITIES

from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.postgresql import insert

load_dotenv()

DATA_DIR = Path(__file__).parent.parent / "data"
CLEAN_FILE = DATA_DIR / "clean" / "clean.csv"

OUTPUT_DIR = DATA_DIR / "warehouse"

MEASURE_COLUMNS = HOURLY_VARIABLES


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
    missing = fact[fact["city_id"].isna()]

    if not missing.empty:
        print("\n=== Missing city_id ===")
        print(missing[["city", "country", "date"]])
    
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

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not defined."
        )

    if database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+psycopg2://",
            1,
        )

    return create_engine(
        database_url,
        pool_pre_ping=True,
    )


def load_to_postgres(
    dim_city: pd.DataFrame,
    dim_time: pd.DataFrame,
    fact: pd.DataFrame,
    engine=None,
    full_refresh: bool = False,
) -> None:
    from sqlalchemy import text

    engine = engine or get_engine()

    initialize_database(engine)

    if full_refresh:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    TRUNCATE TABLE
                        fact_aqi,
                        dim_time,
                        dim_city
                    RESTART IDENTITY CASCADE
                    """
                )
            )

    upsert_dataframe(
        "dim_city",
        dim_city,
        engine,
        ["city_name"],
    )

    upsert_dataframe(
        "dim_time",
        dim_time,
        engine,
        ["full_datetime"],
    )

    upsert_dataframe(
        "fact_aqi",
        fact,
        engine,
        ["city_id", "time_id"],
    )

    print(
        f"[warehouse] Loaded "
        f"{len(dim_city)} cities, "
        f"{len(dim_time)} timestamps, "
        f"{len(fact)} facts"
    )


def build_warehouse(
    clean_df: pd.DataFrame,
    cities: list[City],
    to_postgres: bool = True,
    full_refresh: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    dim_city = build_dim_city(cities)
    dim_time = build_dim_time(clean_df)
    fact = build_fact_aqi(clean_df, dim_city, dim_time)

    check_coherence(fact, dim_city, dim_time)
    export_warehouse(dim_city, dim_time, fact)
    if to_postgres:
        load_to_postgres(
            dim_city,
            dim_time,
            fact,
            full_refresh=full_refresh,
        )
    return dim_city, dim_time, fact

def initialize_database(engine=None) -> None:
    from sqlalchemy import text

    engine = engine or get_engine()

    init_file = Path(__file__).parent.parent.parent / "db" / "init.sql"

    if not init_file.exists():
        raise FileNotFoundError(f"{init_file} not found")

    with open(init_file, "r", encoding="utf-8") as f:
        sql = f.read()

    with engine.begin() as conn:
        conn.execute(text(sql))

    print("[warehouse] Database schema initialized")

def upsert_dataframe(
    table_name: str,
    df: pd.DataFrame,
    engine,
    conflict_columns: list[str],
) -> None:
    """
    Insert rows into PostgreSQL while ignoring duplicates.
    """

    if df.empty:
        return

    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)

    records = df.to_dict(orient="records")

    with engine.begin() as conn:
        stmt = insert(table).values(records)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=conflict_columns
        )
        conn.execute(stmt)

def main():
    if not CLEAN_FILE.exists():
        raise FileNotFoundError(
            f"{CLEAN_FILE} not found. Run build_clean.py first."
        )

    clean_df = pd.read_csv(
        CLEAN_FILE,
        parse_dates=["date"],
    )

    build_warehouse(
        clean_df=clean_df,
        cities=CITIES,
        full_refresh=False,
    )


if __name__ == "__main__":
    main()