import os

import openmeteo_requests
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

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def build_client() -> openmeteo_requests.Client:
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    return openmeteo_requests.Client(session=retry_session)


def find_city(cities: list[City], latitude: float, longitude: float) -> City | None:
    for city in cities:
        if city.match_coordinates(latitude, longitude):
            return city
    return None


def resolve_output_dir(output_dir: str | None = None) -> str:
    out_dir = output_dir or OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    return out_dir
