"""
SoilGrids (ISRIC) API Client
------------------------------
Public REST API — no API key or account needed. Rate-limited, so don't
hammer it in a tight loop; cache results per field/coordinate if you're
calling this often.

Docs: https://rest.isric.org/soilgrids/v2.0/docs

Two endpoints:
  - properties/query    -> numeric soil properties at chosen depths
  - classification/query -> most likely WRB soil classes at a point

Usage:
    from soilgrids import get_soil_properties, get_soil_classification

    props = get_soil_properties(20.0059, 73.7910)
    classes = get_soil_classification(20.0059, 73.7910)
"""

import requests

BASE_URL = "https://rest.isric.org/soilgrids/v2.0"

# Every property SoilGrids v2.0 predicts. Pass a subset to get_soil_properties
# if you only care about a few (fewer properties = faster response).
ALL_PROPERTIES = [
    "bdod",     # Bulk density
    "cec",      # Cation exchange capacity
    "cfvo",     # Coarse fragments volume
    "clay",     # Clay content
    "nitrogen", # Total nitrogen
    "phh2o",    # pH in water
    "sand",     # Sand content
    "silt",     # Silt content
    "soc",      # Soil organic carbon
    "ocd",      # Organic carbon density
    "ocs",      # Organic carbon stock (only valid for depth "0-30cm")
    "wv0010",   # Volumetric water content at 10kPa
    "wv0033",   # Volumetric water content at 33kPa
    "wv1500",   # Volumetric water content at 1500kPa
]

STANDARD_DEPTHS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]

# Some property values are reported "mapped" (scaled integers) rather than
# in their natural unit — SoilGrids' own docs give these conversion factors.
# Divide the raw mean by this to get the value in the natural unit.
_UNIT_DIVISORS = {
    "phh2o": 10.0,      # -> pH
    "wv0010": 100.0,    # -> cm3/cm3 (volume fraction)
    "wv0033": 100.0,
    "wv1500": 100.0,
    "bdod": 100.0,      # -> cg/cm3 -> kg/dm3 (matches SoilGrids docs)
    "cec": 10.0,        # -> cmol(c)/kg
    "cfvo": 10.0,       # -> cm3/dm3 -> %
    "clay": 10.0,       # -> g/kg -> %
    "sand": 10.0,
    "silt": 10.0,
    "nitrogen": 100.0,  # -> cg/kg -> g/kg
    "soc": 10.0,        # -> dg/kg -> g/kg
    "ocd": 10.0,        # -> hg/m3 -> kg/m3
    "ocs": 10.0,        # -> t/ha
}


def get_soil_properties(lat, lon, properties=None, depths=None, value="mean"):
    """
    Fetch numeric soil properties for a point.

    properties: list of property codes (see ALL_PROPERTIES). Defaults to
                a practical subset useful for agriculture: clay, sand,
                silt, soc, phh2o, nitrogen, cec, bdod.
    depths:     list of depth intervals (see STANDARD_DEPTHS). Defaults
                to the topsoil layer "0-5cm" — most relevant for crops.
    value:      "mean" (default), or "Q0.05"/"Q0.5"/"Q0.95"/"uncertainty".

    Returns a flat list of dicts, one per (property, depth) pair:
        [{"property": "clay", "depth": "0-5cm", "value": 24.3, "unit": "%"}, ...]
    Values are already converted from SoilGrids' "mapped" integer units
    into their natural units (%, g/kg, pH, etc).
    """
    properties = properties or ["clay", "sand", "silt", "soc", "phh2o", "nitrogen", "cec", "bdod"]
    depths = depths or ["0-5cm"]

    params = [("lon", lon), ("lat", lat), ("value", value)]
    for p in properties:
        params.append(("property", p))
    for d in depths:
        params.append(("depth", d))

    response = requests.get(f"{BASE_URL}/properties/query", params=params, timeout=30)
    print("SoilGrids properties response status:", response.status_code)
    response.raise_for_status()
    data = response.json()

    rows = []
    for layer in data.get("properties", {}).get("layers", []):
        prop_code = layer.get("name")
        unit = layer.get("unit_measure", {}).get("target_units", "")
        divisor = _UNIT_DIVISORS.get(prop_code, 1.0)
        for depth_entry in layer.get("depths", []):
            depth_label = depth_entry.get("label")
            raw_value = depth_entry.get("values", {}).get(value)
            converted = (raw_value / divisor) if raw_value is not None else None
            rows.append({
                "property": prop_code,
                "depth": depth_label,
                "value": converted,
                "unit": unit,
            })
    return rows


def get_soil_properties_flat(lat, lon, properties=None, depth="0-5cm", value="mean"):
    """
    Convenience wrapper: same as get_soil_properties() but returns a flat
    {property_code: value} dict for a single depth — handy for dropping
    straight into a dashboard metric row or a database column set.
    """
    rows = get_soil_properties(lat, lon, properties=properties, depths=[depth], value=value)
    return {row["property"]: row["value"] for row in rows}


def get_soil_classification(lat, lon, number_classes=5):
    """
    Most likely WRB (World Reference Base) soil classes at a point, with
    probabilities. Returns:
        {
            "top_class": "Cambisols",
            "classes": [{"name": "Cambisols", "probability": 42.1}, ...]
        }
    """
    params = {"lon": lon, "lat": lat, "number_classes": number_classes}
    response = requests.get(f"{BASE_URL}/classification/query", params=params, timeout=30)
    print("SoilGrids classification response status:", response.status_code)
    response.raise_for_status()
    data = response.json()

    wrb = data.get("wrb_class_probability", []) or []
    classes = [{"name": name, "probability": prob} for name, prob in wrb]
    top_class = data.get("wrb_class_name") or (classes[0]["name"] if classes else None)

    return {"top_class": top_class, "classes": classes}


if __name__ == "__main__":
    # Quick manual test — Nashik, India (matches the app's default coords)
    lat, lon = 20.0059, 73.7910

    print("\n=== SOIL PROPERTIES (topsoil, 0-5cm) ===")
    for row in get_soil_properties(lat, lon):
        print(f"  {row['property']:10s} {row['depth']:8s} {row['value']} {row['unit']}")

    print("\n=== SOIL CLASSIFICATION ===")
    print(get_soil_classification(lat, lon))
