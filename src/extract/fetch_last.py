import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ..model.city import City
from .common import HOURLY_VARIABLES, find_city, resolve_output_dir
from ..model.city import CITIES

API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def fetch_last_hourly_aqi(cities: list[City]) -> list:
    from .common import build_client

    client = build_client()
    params = {
        "latitude": [c.latitude for c in cities],
        "longitude": [c.longitude for c in cities],
        "hourly": HOURLY_VARIABLES,
        "past_hours": 1,
    }
    return client.weather_api(API_URL, params=params)


def export_to_csv(
    responses: list, cities: list[City], output_dir: str | None = None
):
    out_dir = resolve_output_dir(output_dir)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    for response in responses:
        city = find_city(cities, response.Latitude(), response.Longitude())
        city_label = (
            city.name if city else f"{response.Latitude()}_{response.Longitude()}"
        )

        hourly = response.Hourly()

        hourly_data = {
            "date": pd.to_datetime(
                hourly.Time(), unit="s", utc=True
            ).isoformat()
        }

        for i, var_name in enumerate(HOURLY_VARIABLES):
            hourly_data[var_name] = hourly.Variables(i).ValuesAsNumpy()[0]
        hourly_data["country"] = city.country if city is not None else None
        hourly_data["city"] = city.name if city is not None else None

        df = pd.DataFrame([hourly_data])

        filename = f"{city_label.lower().replace(' ', '_')}_{timestamp}.csv"
        csv_path = os.path.join(out_dir, filename)
        df.to_csv(csv_path, index=False)
        print(f"Exported last hourly AQI for {city_label} to {csv_path}")

def main():
    responses = fetch_last_hourly_aqi(CITIES)

    export_to_csv(
        responses=responses,
        cities=CITIES,
        output_dir=Path(__file__).parent.parent / "data" / "raw" / "hourly",
    )


if __name__ == "__main__":
    main()