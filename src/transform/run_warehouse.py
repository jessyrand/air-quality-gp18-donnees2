from pathlib import Path

from ..extract.fetch_last import fetch_last_hourly_aqi
from ..model.city import CITIES
from .build_warehouse import build_warehouse
from .merge_history import clean_dataframe, load_history_csv
from .merge_last import transform_last_hourly_aqi

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

history_by_city = {
    c.name: clean_dataframe(
        load_history_csv(RAW_DIR / f"{c.name.lower().replace(' ', '_')}.csv")
    )
    for c in CITIES
}

last_responses = fetch_last_hourly_aqi(CITIES)
last_hour_rows = transform_last_hourly_aqi(last_responses, CITIES)

dim_city, dim_time, fact = build_warehouse(history_by_city, last_hour_rows, CITIES)

print(dim_city)
print(dim_time)
print(fact)
