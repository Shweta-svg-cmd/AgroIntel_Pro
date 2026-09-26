"""
Agromonitoring (Agro API) Client
-----------------------------------
Needs a free API key from https://agromonitoring.com (separate signup from
regular OpenWeather, even though it's the same company — the appid from
openweather.py will NOT work here).

.env file should contain:
    AGROMONITORING_API_KEY=...

Nearly everything in this API is scoped to a "polygon" (a field boundary
you register once via create_polygon()) rather than a raw lat/lon — create
the polygon first, keep its returned id, then pass that id to the other
functions.

Docs: https://agromonitoring.com/api
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AGROMONITORING_API_KEY", "")
BASE_URL = "http://api.agromonitoring.com/agro/1.0"


def _check_key():
    if not API_KEY:
        raise RuntimeError(
            "AGROMONITORING_API_KEY is not set. Get a free key at "
            "https://agromonitoring.com/ and add it to your .env file."
        )


# ---------------------------------------------------------------------------
# Polygons — register a field boundary once, reuse its id everywhere else
# ---------------------------------------------------------------------------

def create_polygon(name, geo_json_coordinates):
    """
    Register a field boundary and get back a polygon id to use in every
    other call. `geo_json_coordinates` is a GeoJSON Polygon "coordinates"
    array: a list containing one ring of [lon, lat] pairs, first and last
    point identical (closed ring), e.g.:

        [[
            [73.7890, 20.0040],
            [73.7930, 20.0040],
            [73.7930, 20.0075],
            [73.7890, 20.0075],
            [73.7890, 20.0040],
        ]]

    Returns the full polygon record (includes "id", "area" in hectares,
    and "center").
    """
    _check_key()
    body = {
        "name": name,
        "geo_json": {
            "type": "Feature",
            "properties": {},
            "geometry": {"type": "Polygon", "coordinates": geo_json_coordinates},
        },
    }
    response = requests.post(
        f"{BASE_URL}/polygons",
        params={"appid": API_KEY, "duplicated": "true"},
        json=body,
        timeout=30,
    )
    print("Agromonitoring create_polygon response status:", response.status_code)
    response.raise_for_status()
    return response.json()


def list_polygons():
    """List every polygon registered under this API key."""
    _check_key()
    response = requests.get(f"{BASE_URL}/polygons", params={"appid": API_KEY}, timeout=30)
    print("Agromonitoring list_polygons response status:", response.status_code)
    response.raise_for_status()
    return response.json()


def delete_polygon(polygon_id):
    _check_key()
    response = requests.delete(f"{BASE_URL}/polygons/{polygon_id}", params={"appid": API_KEY}, timeout=30)
    print("Agromonitoring delete_polygon response status:", response.status_code)
    return response.status_code == 200


# ---------------------------------------------------------------------------
# Current conditions by polygon
# ---------------------------------------------------------------------------

def get_current_weather(polygon_id):
    """Current weather for the polygon's centroid (same shape as OpenWeather's /weather)."""
    _check_key()
    response = requests.get(f"{BASE_URL}/weather", params={"polyid": polygon_id, "appid": API_KEY}, timeout=15)
    print("Agromonitoring current weather response status:", response.status_code)
    response.raise_for_status()
    return response.json()


def get_weather_forecast(polygon_id):
    """Multi-day forecast for the polygon's centroid."""
    _check_key()
    response = requests.get(f"{BASE_URL}/weather/forecast", params={"polyid": polygon_id, "appid": API_KEY}, timeout=15)
    print("Agromonitoring forecast response status:", response.status_code)
    response.raise_for_status()
    return response.json()


def get_current_soil(polygon_id):
    """
    Current soil moisture/temperature for a polygon, updated twice daily.
    Returns: {"dt": unix_time, "t0": surface_temp_K, "t10": temp_at_10cm_K, "moisture": m3/m3}
    """
    _check_key()
    response = requests.get(f"{BASE_URL}/soil", params={"polyid": polygon_id, "appid": API_KEY}, timeout=15)
    print("Agromonitoring current soil response status:", response.status_code)
    response.raise_for_status()
    return response.json()


def get_soil_history(polygon_id, start, end):
    """
    Historical soil moisture/temperature. `start`/`end` are unix timestamps
    (UTC). Data available from March 2019 onward.
    """
    _check_key()
    params = {"polyid": polygon_id, "start": start, "end": end, "appid": API_KEY}
    response = requests.get(f"{BASE_URL}/soil/history", params=params, timeout=30)
    print("Agromonitoring soil history response status:", response.status_code)
    response.raise_for_status()
    return response.json()


def get_current_uvi(polygon_id):
    """Current UV index for the polygon."""
    _check_key()
    response = requests.get(f"{BASE_URL}/uvi", params={"polyid": polygon_id, "appid": API_KEY}, timeout=15)
    print("Agromonitoring current UVI response status:", response.status_code)
    response.raise_for_status()
    return response.json()


def get_uvi_forecast(polygon_id, days=7):
    """Forecasted UV index for the next `days` days."""
    _check_key()
    params = {"polyid": polygon_id, "cnt": days, "appid": API_KEY}
    response = requests.get(f"{BASE_URL}/uvi/forecast", params=params, timeout=15)
    print("Agromonitoring UVI forecast response status:", response.status_code)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# NDVI / EVI — vegetation health from satellite imagery
# ---------------------------------------------------------------------------

def get_ndvi_history(polygon_id, start, end, source=None):
    """
    Historical NDVI/EVI vegetation index stats for a polygon between two
    unix timestamps. Each entry covers one satellite pass and includes
    mean/median/min/max/std NDVI across the field for that pass — this is
    the number you'd chart over a season to see crop vigor trend up or down.

    source: optional, "l8" (Landsat-8) or "s2" (Sentinel-2) to restrict
            to one satellite; omit to get all available passes.
    """
    _check_key()
    params = {"polyid": polygon_id, "start": start, "end": end, "appid": API_KEY}
    if source:
        params["type"] = source
    response = requests.get(f"{BASE_URL}/ndvi/history", params=params, timeout=30)
    print("Agromonitoring NDVI history response status:", response.status_code)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    if not API_KEY:
        print("Set AGROMONITORING_API_KEY in .env to run this test.")
    else:
        # Small rectangle around the app's default Nashik coordinates
        polygon = create_polygon("AgroIntel test field", [[
            [73.7890, 20.0040],
            [73.7930, 20.0040],
            [73.7930, 20.0075],
            [73.7890, 20.0075],
            [73.7890, 20.0040],
        ]])
        print("\n=== POLYGON CREATED ===")
        print(polygon)

        poly_id = polygon["id"]

        print("\n=== CURRENT SOIL ===")
        print(get_current_soil(poly_id))

        print("\n=== CURRENT UVI ===")
        print(get_current_uvi(poly_id))
