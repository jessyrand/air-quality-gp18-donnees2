import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.extract.common import (
    HOURLY_VARIABLES,
    build_client,
    find_city,
    resolve_output_dir,
)
from src.model.city import CITIES, City

API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def ensure_directories():
    (DATA_DIR / "raw" / "history").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "raw" / "hourly").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "clean").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "warehouse").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "cache").mkdir(parents=True, exist_ok=True)


def fetch_history_hourly_aqi(
    cities: list[City],
    start: str,
    end: str,
) -> list:
    client = build_client()

    params = {
        "latitude": [c.latitude for c in cities],
        "longitude": [c.longitude for c in cities],
        "hourly": HOURLY_VARIABLES,
        "start_date": start,
        "end_date": end,
    }

    return client.weather_api(API_URL, params=params)


def export_to_csv(
    responses: list,
    cities: list[City],
    output_dir: str | Path | None = None,
):
    out_dir = Path(resolve_output_dir(output_dir))

    for response in responses:
        city = find_city(cities, response.Latitude(), response.Longitude())
        city_label = (
            city.name
            if city
            else f"{response.Latitude()}_{response.Longitude()}"
        )

        hourly = response.Hourly()

        hourly_data = {
            "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left",
            )
        }

        for i, var_name in enumerate(HOURLY_VARIABLES):
            hourly_data[var_name] = hourly.Variables(i).ValuesAsNumpy()

        hourly_data["country"] = city.country if city else None

        df = pd.DataFrame(hourly_data)

        csv_path = out_dir / f"{city_label.lower().replace(' ', '_')}_history.csv"

        df.to_csv(csv_path, index=False)

        print(f"Exported {len(df)} rows to {csv_path}")

    print("History backfill completed.")


def main():
    ensure_directories()

    responses = fetch_history_hourly_aqi(
        cities=CITIES,
        start="2026-07-01",
        end=datetime.now().strftime("%Y-%m-%d"),
    )

    export_to_csv(
        responses=responses,
        cities=CITIES,
        output_dir=DATA_DIR / "raw" / "history",
    )


if __name__ == "__main__":
    main()