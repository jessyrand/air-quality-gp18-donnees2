import os

import pandas as pd

from ..model.city import City
from .common import HOURLY_VARIABLES, build_client, find_city, resolve_output_dir

API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def fetch_history_hourly_aqi(
    cities: list[City], start: str, end: str
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


def export_to_csv(responses: list, cities: list[City], output_dir: str | None = None):
    out_dir = resolve_output_dir(output_dir)

    for response in responses:
        city = find_city(cities, response.Latitude(), response.Longitude())
        city_label = city.name if city else f"{response.Latitude()}_{response.Longitude()}"

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

        df = pd.DataFrame(data=hourly_data)

        csv_path = os.path.join(out_dir, f"{city_label.lower().replace(' ', '_')}.csv")
        df.to_csv(csv_path, index=False)
        print(f"Exported {len(df)} rows to {csv_path}")
