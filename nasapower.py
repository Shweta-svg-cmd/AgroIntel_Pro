"""
NASA POWER Agroclimatology API Client
--------------------------------------
No auth required. Fetches daily point data (temperature, rainfall,
humidity, solar radiation, wind, soil moisture) for a given lat/lon
and date range — useful for combining with field/farm coordinates
from other sources (e.g. your John Deere field boundaries later).

Docs: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
"""

from datetime import datetime, timedelta

import requests

BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PROCESSING_LAG_DAYS = 3  # NASA POWER typically lags 2-3 days behind real-time

# Common agro-relevant parameters. Full list:
# https://power.larc.nasa.gov/parameters/
DEFAULT_PARAMETERS = [
    "T2M",              # Temperature at 2m (°C)
    "T2M_MAX",          # Max temp
    "T2M_MIN",          # Min temp
    "PRECTOTCORR",      # Precipitation (mm/day)
    "RH2M",             # Relative humidity at 2m (%)
    "ALLSKY_SFC_SW_DWN",  # Solar radiation (kWh/m^2/day) — sunlight for crops
    "WS2M",             # Wind speed at 2m (m/s)
    "GWETTOP",          # Surface soil wetness (0-1)
    "GWETROOT",         # Root zone soil wetness (0-1)
]


def get_agro_weather(lat, lon, start_date, end_date, parameters=None, community="AG"):
    """
    Fetch daily agro-climatology data for a point.

    lat, lon      : float coordinates
    start_date    : "YYYYMMDD" string
    end_date      : "YYYYMMDD" string
    parameters    : list of NASA POWER parameter codes (defaults to DEFAULT_PARAMETERS)
    community     : "AG" (agroclimatology), "RE" (renewable energy), or "SB" (sustainable buildings)

    Returns a dict of {parameter: {date: value}}
    """
    params = {
        "parameters": ",".join(parameters or DEFAULT_PARAMETERS),
        "community": community,
        "longitude": lon,
        "latitude": lat,
        "start": start_date,
        "end": end_date,
        "format": "JSON",
    }

    headers = {"User-Agent": "AgroIntel-Pro/1.0 (agriculture data client)"}

    response = requests.get(BASE_URL, params=params, headers=headers, timeout=30)
    print("NASA POWER response status:", response.status_code)

    if response.status_code != 200:
        print(response.text)

    response.raise_for_status()
    data = response.json()

    return data["properties"]["parameter"]


def get_agro_weather_flat(lat, lon, start_date, end_date, parameters=None, community="AG"):
    """
    Same as get_agro_weather but reshaped into a list of per-day dicts,
    easier to drop straight into a table/UI/DataFrame:

        [{"date": "20260101", "T2M": 21.3, "PRECTOTCORR": 0.0, ...}, ...]
    """
    raw = get_agro_weather(lat, lon, start_date, end_date, parameters, community)

    param_names = list(raw.keys())
    dates = list(raw[param_names[0]].keys())

    rows = []
    for date in dates:
        row = {"date": date}
        for p in param_names:
            row[p] = raw[p][date]
        rows.append(row)

    return rows


def safe_end_date():
    """Latest date NASA POWER has likely finished processing."""
    return (datetime.utcnow() - timedelta(days=PROCESSING_LAG_DAYS)).strftime("%Y%m%d")


if __name__ == "__main__":
    # Example: last 7 processed days of weather for a field near Nashik, Maharashtra
    lat, lon = 20.0059, 73.7910

    end = safe_end_date()
    start = (datetime.strptime(end, "%Y%m%d") - timedelta(days=6)).strftime("%Y%m%d")

    rows = get_agro_weather_flat(
        lat=lat,
        lon=lon,
        start_date=start,
        end_date=end,
    )

    print("\n=== DAILY AGRO WEATHER ===")
    for row in rows:
        print(row)