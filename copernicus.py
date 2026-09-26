"""
Copernicus Data Space Ecosystem (CDSE) Client
-------------------------------------------------
Free account required (register at https://dataspace.copernicus.eu/), but
product *search* itself needs no authentication at all — only downloading
an actual product file requires a token.

.env file should contain:
    COPERNICUS_USERNAME=...
    COPERNICUS_PASSWORD=...

This is the successor to the old "Copernicus Open Access Hub" / SciHub —
if you find older tutorials referencing scihub.copernicus.eu, that service
is retired; this file targets the current dataspace.copernicus.eu APIs.

Two APIs are wrapped here:
  - OData catalogue: search for Sentinel products by collection/date/area
    (search_products) and download a found product (download_product).
  - Nothing here processes imagery into NDVI/etc — that needs the separate
    Sentinel Hub Process API (also under CDSE) with actual band math, which
    is a bigger undertaking than a single client file; this covers
    discovery + download, which is the first 80% of most integrations.

Docs: https://documentation.dataspace.copernicus.eu/APIs/OData.html
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("COPERNICUS_USERNAME", "")
PASSWORD = os.getenv("COPERNICUS_PASSWORD", "")

TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
ODATA_BASE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1"
ZIPPER_BASE_URL = "https://zipper.dataspace.copernicus.eu/odata/v1"

# Public CDSE OAuth client — this is CDSE's own published public client id
# for the password grant, not a secret specific to your app.
_OAUTH_CLIENT_ID = "cdse-public"


def get_access_token(username=None, password=None):
    """
    OAuth2 password-grant login. Only needed for downloading actual product
    files — search_products() below works without calling this at all.
    """
    username = username or USERNAME
    password = password or PASSWORD
    if not username or not password:
        raise RuntimeError(
            "COPERNICUS_USERNAME / COPERNICUS_PASSWORD not set. Register free "
            "at https://dataspace.copernicus.eu/ and add credentials to .env."
        )

    data = {
        "client_id": _OAUTH_CLIENT_ID,
        "username": username,
        "password": password,
        "grant_type": "password",
    }
    response = requests.post(TOKEN_URL, data=data, timeout=20)
    print("Copernicus token response status:", response.status_code)
    response.raise_for_status()
    return response.json()["access_token"]


def _bbox_to_wkt_polygon(min_lon, min_lat, max_lon, max_lat):
    """Turns a bounding box into a WKT POLYGON string for the area filter."""
    return (
        f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, "
        f"{max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
    )


def search_products(collection, start_date, end_date, bbox=None, wkt_polygon=None,
                     product_type=None, cloud_cover_max=None, top=20):
    """
    Search the CDSE catalogue for satellite products. No auth needed.

    collection:  "SENTINEL-1", "SENTINEL-2", "SENTINEL-3", "SENTINEL-5P", etc.
    start_date, end_date: ISO strings, e.g. "2026-06-01T00:00:00.000Z"
    bbox:        optional (min_lon, min_lat, max_lon, max_lat) tuple — used
                 if wkt_polygon isn't given.
    wkt_polygon: optional WKT POLYGON string for an exact field boundary,
                 takes priority over bbox if both are given.
    product_type: optional, e.g. "S2MSI2A" (Sentinel-2 L2A surface reflectance).
    cloud_cover_max: optional int 0-100, filters Sentinel-2 by cloud cover %.
    top:         max results to return (CDSE default page size is 20).

    Returns a list of product dicts (raw OData records) — each has at
    least "Id", "Name", "ContentDate", "Footprint", "S3Path".
    """
    filters = [f"Collection/Name eq '{collection}'"]

    if wkt_polygon:
        filters.append(f"OData.CSC.Intersects(area=geography'SRID=4326;{wkt_polygon}')")
    elif bbox:
        wkt = _bbox_to_wkt_polygon(*bbox)
        filters.append(f"OData.CSC.Intersects(area=geography'SRID=4326;{wkt}')")

    filters.append(f"ContentDate/Start gt {start_date}")
    filters.append(f"ContentDate/Start lt {end_date}")

    if product_type:
        filters.append(
            "Attributes/OData.CSC.StringAttribute/any("
            f"att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq '{product_type}')"
        )
    if cloud_cover_max is not None:
        filters.append(
            "Attributes/OData.CSC.DoubleAttribute/any("
            f"att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt {cloud_cover_max})"
        )

    params = {"$filter": " and ".join(filters), "$top": top, "$orderby": "ContentDate/Start desc"}

    response = requests.get(f"{ODATA_BASE_URL}/Products", params=params, timeout=30)
    print("Copernicus search response status:", response.status_code)
    response.raise_for_status()
    return response.json().get("value", [])


def get_product(product_id):
    """Fetch full metadata for a single product by its OData id (GUID)."""
    response = requests.get(f"{ODATA_BASE_URL}/Products({product_id})", timeout=20)
    print("Copernicus get_product response status:", response.status_code)
    response.raise_for_status()
    return response.json()


def download_product(product_id, output_path, access_token=None):
    """
    Download a product's full .zip archive. Requires auth — pass an
    access_token from get_access_token(), or one will be fetched using
    COPERNICUS_USERNAME/PASSWORD from .env. Sentinel product archives can
    be several GB, so this streams to disk in chunks.
    """
    token = access_token or get_access_token()
    url = f"{ZIPPER_BASE_URL}/Products({product_id})/$value"
    headers = {"Authorization": f"Bearer {token}"}

    with requests.get(url, headers=headers, stream=True, timeout=60) as response:
        print("Copernicus download response status:", response.status_code)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    return output_path


if __name__ == "__main__":
    # Quick manual test — search only, no auth/download needed for this part.
    # Small bbox around Nashik, India (matches the app's default coords).
    results = search_products(
        collection="SENTINEL-2",
        start_date="2026-06-01T00:00:00.000Z",
        end_date="2026-06-30T00:00:00.000Z",
        bbox=(73.75, 19.97, 73.83, 20.04),
        product_type="S2MSI2A",
        cloud_cover_max=30,
        top=5,
    )
    print(f"\n=== FOUND {len(results)} PRODUCTS ===")
    for p in results:
        print(f"  {p.get('Name')}  (id={p.get('Id')})")
