import math
from typing import List, Dict


def predict_route(lat: float, lon: float, heading_deg: float, speed_kmh: float, steps: int = 10, step_seconds: int = 30) -> List[Dict]:
    # Simple linear extrapolation using approximate meters/degree conversion
    # Convert speed to m/s
    speed_ms = max(speed_kmh, 0) * 1000 / 3600.0
    heading_rad = math.radians(heading_deg % 360)

    path = []
    curr_lat = lat
    curr_lon = lon
    for i in range(1, steps + 1):
        dt = i * step_seconds
        distance_m = speed_ms * step_seconds
        # Approx meters per degree latitude ~ 111,111 m; longitude scales by cos(lat)
        dlat_deg = (distance_m * math.cos(heading_rad)) / 111_111.0
        dlon_deg = (distance_m * math.sin(heading_rad)) / (111_111.0 * max(math.cos(math.radians(curr_lat)), 1e-3))
        curr_lat += dlat_deg
        curr_lon += dlon_deg
        path.append({"lat": curr_lat, "lon": curr_lon, "t": dt})
    return path