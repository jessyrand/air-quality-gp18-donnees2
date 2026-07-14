import pandas as pd

from ..model.city import City
from .common import HOURLY_VARIABLES, find_city


def transform_last_hourly_aqi(
    responses: list,
    cities: list[City],
) -> list[tuple[str, pd.DataFrame]]:
    transformed = []

    for response in responses:
        city = find_city(
            cities,
            response.Latitude(),
            response.Longitude(),
        )
        city_label = (
            city.name
            if city is not None
            else f"{response.Latitude()}_{response.Longitude()}"
        )

        hourly = response.Hourly()

        row = {
            "date": pd.to_datetime(
                hourly.Time(),
                unit="s",
                utc=True,
            )
        }

        for i, variable in enumerate(HOURLY_VARIABLES):
            row[variable] = hourly.Variables(i).ValuesAsNumpy()[0]

        row["country"] = city.country if city is not None else None
        row["city"] = city.name if city is not None else None

        df = pd.DataFrame([row])
        df["date"] = pd.to_datetime(df["date"], utc=True)
        df = df.drop_duplicates()
        df = df.dropna(how="all")
        df = df.sort_values("date")
        df = df.reset_index(drop=True)

        transformed.append((city_label, df))

    return transformed