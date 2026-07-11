from datetime import datetime

from src.extract.fetch_history import export_to_csv, fetch_history_hourly_aqi
from src.model.city import CITIES

import os

def main():
    responses = fetch_history_hourly_aqi(
        cities=CITIES,
        start="2026-07-01",
        end=datetime.now().strftime("%Y-%m-%d"),
    )
    export_to_csv(cities=CITIES, responses=responses, output_dir=os.path.join(os.path.dirname(__file__), "data", "raw"))


if __name__ == "__main__":
    main()
