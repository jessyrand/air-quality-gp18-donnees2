import pandas as pd

from ..model.city import City
from .common import HOURLY_VARIABLES, find_city


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