import os

import pandas as pd

from ..model.city import City
from .common import HOURLY_VARIABLES, build_client, find_city, resolve_output_dir


def merge_history_csv( new_df: pd.DataFrame,csv_path: str,) -> pd.DataFrame:
 
    if not os.path.exists(csv_path):
        new_df.to_csv(csv_path, index=False)
        print(f"Created history file: {csv_path}")
        return new_df

    old_df = pd.read_csv(csv_path)
    old_df["date"] = pd.to_datetime(old_df["date"], utc=True)
    new_df["date"] = pd.to_datetime(new_df["date"], utc=True)

    merged_df = pd.concat([old_df, new_df],ignore_index=True)

    merged_df = merged_df.drop_duplicates(subset=["date"],keep="last")

    merged_df = merged_df.sort_values("date")

    merged_df.to_csv(csv_path, index=False)

    print(
        f"Merged {len(new_df)} new rows "
        f"-> total {len(merged_df)} rows in {csv_path}"
    )

    return merged_df

def merge_history(
    responses: list,
    cities: list[City],
    output_dir: str | None = None,
):
 
    out_dir = resolve_output_dir(output_dir)

    for response in responses:

        city = find_city(
            cities,
            response.Latitude(),
            response.Longitude(),
        )

        city_label = (
            city.name
            if city
            else f"{response.Latitude()}_{response.Longitude()}"
        )

        hourly = response.Hourly()

        hourly_data = {
            "date": pd.date_range(
                start=pd.to_datetime(
                    hourly.Time(),
                    unit="s",
                    utc=True,
                ),
                end=pd.to_datetime(
                    hourly.TimeEnd(),
                    unit="s",
                    utc=True,
                ),
                freq=pd.Timedelta(
                    seconds=hourly.Interval()
                ),
                inclusive="left",
            )
        }

        for i, variable in enumerate(HOURLY_VARIABLES):
            hourly_data[variable] = (
                hourly.Variables(i).ValuesAsNumpy()
            )

        hourly_data["country"] = (
            city.country if city else None
        )

        new_df = pd.DataFrame(hourly_data)

        csv_path = os.path.join(
            out_dir,
            f"{city_label.lower().replace(' ', '_')}.csv",
        )

        merge_history_csv(
            new_df=new_df,
            csv_path=csv_path,
        )