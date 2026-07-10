import os

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

from ..model.city import City

HOURLY_VARIABLES = [
    "pm10",
    "pm2_5",
    "carbon_monoxide",
    "carbon_dioxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
    "methane",
    "european_aqi",
    "us_aqi",
]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "output")


def _build_client() -> openmeteo_requests.Client:
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    return openmeteo_requests.Client(session=retry_session)


def fetch_history_hourly_aqi(
    cities: list[City], start: str, end: str
) -> list:
    client = _build_client()

    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": [c.latitude for c in cities],
        "longitude": [c.longitude for c in cities],
        "hourly": HOURLY_VARIABLES,
        "start_date": start,
        "end_date": end,
    }
    return client.weather_api(url, params=params)


def _find_city(
    cities: list[City], latitude: float, longitude: float
) -> City | None:
    for city in cities:
        if city.match_coordinates(latitude, longitude):
            return city
    return None


def export_to_csv(responses: list, cities: list[City], output_dir: str | None = None):
    out_dir = output_dir or OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)

    for response in responses:
        city = _find_city(cities, response.Latitude(), response.Longitude())
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
