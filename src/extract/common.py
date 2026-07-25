import os
from pathlib import Path

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

# Répertoire data du projet
DATA_DIR = Path(__file__).resolve().parents[2] / "data"

OUTPUT_DIR = DATA_DIR


def build_client() -> openmeteo_requests.Client:
    cache_dir = DATA_DIR / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_session = requests_cache.CachedSession(
        str(cache_dir / "openmeteo_cache"),
        expire_after=3600,
    )

    retry_session = retry(
        cache_session,
        retries=5,
        backoff_factor=0.2,
    )

    return openmeteo_requests.Client(session=retry_session)


def find_city(
    cities: list[City],
    latitude: float,
    longitude: float,
) -> City | None:
    for city in cities:
        if city.match_coordinates(latitude, longitude):
            return city
    return None


def resolve_output_dir(output_dir: str | None = None) -> str:
    out_dir = Path(output_dir) if output_dir else OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    return str(out_dir)