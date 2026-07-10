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

