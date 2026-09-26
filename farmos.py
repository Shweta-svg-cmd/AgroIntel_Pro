"""
farmOS API Client
--------------------
IMPORTANT — this one's different from the others: farmOS is open-source
software you (or someone) self-hosts, not a shared public API with one
fixed URL. Every farmOS instance lives at its own address (e.g.
https://yourfarm.farmos.net or a self-hosted domain). Before any of this
works you need:
  1. A running farmOS instance (farmOS.net hosted, or self-hosted via
     Docker/Farmier).
  2. An OAuth2 client registered on that instance — farmOS ships with a
     default public client named "farm" (no secret) for first-party apps,
     or you can create your own under Admin > People > API Clients.

.env file should contain:
    FARMOS_URL=https://yourfarm.farmos.net
    FARMOS_CLIENT_ID=farm
    FARMOS_CLIENT_SECRET=            # blank is normal for the default "farm" client
    FARMOS_USERNAME=...
    FARMOS_PASSWORD=...

farmOS speaks JSON:API (a Drupal standard), so every resource lives at
/api/{entity_type}/{bundle}, e.g. /api/asset/land, /api/log/observation.
Bundle names are configurable per-instance, so the constants below cover
farmOS's own defaults — adjust FIELD_ASSET_TYPES / LOG_TYPES if your
instance uses custom bundles.

Docs: https://farmos.org/development/api/
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

FARMOS_URL = os.getenv("FARMOS_URL", "").rstrip("/")
CLIENT_ID = os.getenv("FARMOS_CLIENT_ID", "farm")
CLIENT_SECRET = os.getenv("FARMOS_CLIENT_SECRET", "")
USERNAME = os.getenv("FARMOS_USERNAME", "")
PASSWORD = os.getenv("FARMOS_PASSWORD", "")

# Default farmOS asset bundles (a "field" in farmOS is asset type "land").
ASSET_TYPES = ["land", "plant", "animal", "equipment", "water", "structure", "sensor"]

# Default farmOS log bundles (this is where actual farm activity lives —
# what was planted, harvested, applied, observed, moved, etc).
LOG_TYPES = ["activity", "harvest", "input", "observation", "seeding", "transplanting", "maintenance"]


def _check_config():
    if not FARMOS_URL:
        raise RuntimeError(
            "FARMOS_URL is not set. Point it at your farmOS instance "
            "(e.g. https://yourfarm.farmos.net) in .env."
        )


def get_access_token():
    """
    OAuth2 password-grant login against the farmOS instance. Returns the
    raw token response dict (has "access_token", "refresh_token", "expires_in").
    """
    _check_config()
    if not USERNAME or not PASSWORD:
        raise RuntimeError("FARMOS_USERNAME / FARMOS_PASSWORD not set in .env.")

    data = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": USERNAME,
        "password": PASSWORD,
        "scope": "farmos_restws_scope",  # farmOS's standard default scope name
    }
    response = requests.post(f"{FARMOS_URL}/oauth/token", data=data, timeout=20)
    print("farmOS token response status:", response.status_code)
    response.raise_for_status()
    return response.json()


def _headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
    }


def _get_jsonapi(access_token, path, params=None):
    _check_config()
    response = requests.get(f"{FARMOS_URL}{path}", headers=_headers(access_token), params=params, timeout=30)
    print(f"farmOS GET {path} response status:", response.status_code)
    response.raise_for_status()
    return response.json()


def get_assets(access_token, bundle="land", filters=None, page_size=50):
    """
    Fetch assets of a given bundle (default "land" — farmOS's term for
    fields/parcels). Other common bundles: "plant" (a planting/crop batch),
    "animal", "equipment".

    filters: optional dict of JSON:API filter params, e.g.
             {"filter[status]": "active"}

    Returns a flat list of simplified dicts:
        [{"id": "...", "name": "...", "status": "active", "attributes": {...}}, ...]
    """
    params = {"page[limit]": page_size}
    if filters:
        params.update(filters)

    data = _get_jsonapi(access_token, f"/api/asset/{bundle}", params=params)
    return _flatten_jsonapi(data)


def get_logs(access_token, bundle="observation", filters=None, page_size=50):
    """
    Fetch logs of a given bundle (default "observation"). Other common
    bundles: "harvest", "input" (fertilizer/spray application), "seeding",
    "activity", "maintenance". Logs are farmOS's record of things that
    actually happened on the farm — this is the closest equivalent to
    AgroIntel's own soil-analysis / compliance tables.

    Returns a flat list of simplified dicts.
    """
    params = {"page[limit]": page_size}
    if filters:
        params.update(filters)

    data = _get_jsonapi(access_token, f"/api/log/{bundle}", params=params)
    return _flatten_jsonapi(data)


def get_areas(access_token, page_size=50):
    """Convenience alias for get_assets(bundle='land') — fields/areas."""
    return get_assets(access_token, bundle="land", page_size=page_size)


def get_quantities(access_token, filters=None, page_size=50):
    """
    Quantities are farmOS's generic measurement records (attached to logs)
    — yield amounts, input rates, soil test readings, etc.
    """
    params = {"page[limit]": page_size}
    if filters:
        params.update(filters)
    data = _get_jsonapi(access_token, "/api/quantity/standard", params=params)
    return _flatten_jsonapi(data)


def _flatten_jsonapi(data):
    """
    JSON:API responses wrap everything in {"data": [{"id", "type",
    "attributes": {...}, "relationships": {...}}, ...]}. This pulls out
    the useful bits into plain flat dicts so callers don't have to know
    JSON:API's structure.
    """
    rows = []
    for item in data.get("data", []):
        attrs = item.get("attributes", {}) or {}
        rows.append({
            "id": item.get("id"),
            "type": item.get("type"),
            "name": attrs.get("name"),
            "status": attrs.get("status"),
            "attributes": attrs,
        })
    return rows


if __name__ == "__main__":
    if not FARMOS_URL:
        print("Set FARMOS_URL (and credentials) in .env to run this test.")
    else:
        tokens = get_access_token()
        access_token = tokens["access_token"]

        print("\n=== FIELDS (asset/land) ===")
        for field in get_areas(access_token):
            print(f"  {field['name']} ({field['id']}) — status: {field['status']}")

        print("\n=== RECENT OBSERVATIONS ===")
        for log in get_logs(access_token, bundle="observation"):
            print(f"  {log['name']} ({log['id']})")
