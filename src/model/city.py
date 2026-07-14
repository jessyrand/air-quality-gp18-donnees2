import math


class City:
    def __init__(self, name: str, latitude: float, longitude: float, country: str) -> None:
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.country = country

    def match_coordinates(self, lat: float, long: float) -> bool:
        return math.isclose(self.latitude, lat, abs_tol=0.1) and math.isclose(
            self.longitude, long, abs_tol=0.1
        )

CITIES = [
    City("Paris",48.8534951,2.3483915, "France"),
    City("Tokyo",35.6768601,139.7638947, "Japan"),
    City("Sydney",-33.8698439,151.2082848, "Australia"),
    City("New York", 40.7127281,-74.0060152, "USA"),
    City("Antananarivo", -18.9100122,47.5255809, "Madagascar")
]
