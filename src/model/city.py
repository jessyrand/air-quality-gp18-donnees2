import math


class City:
    def __init__(self, name: str, latitude: float, longitude: float) -> None:
        self.name = name
        self.latitude = latitude
        self.longitude = longitude

    def match_coordinates(self, lat: float, long: float) -> bool:
        return math.isclose(self.latitude, lat, abs_tol=0.1) and math.isclose(
            self.longitude, long, abs_tol=0.1
        )
