"""
John Deere API Client
----------------------
Handles OAuth2 login (authorization code flow), token persistence/refresh,
and fetching data using the HATEOAS links returned by the API instead of
hardcoded URLs, wherever John Deere actually provides those links.

SCOPE OF THIS FILE (per the access confirmation from John Deere):
    Approved  : Organizations, Equipment, Machine Locations,
                Machine Device State Report, Machine Hours Of Operation,
                Map Layers, Machine Alerts, ISO 15143-3
    NOT approved: Fields, Farms, Boundaries, Users, Assets, Files, Product

This file intentionally does NOT call Fields/Farms/Boundaries/Assets/Files —
those will 403 for this app registration. `get_related()` is still here as a
generic org-link fetcher in case your access changes later, but nothing in
app_jd.py calls it for denied resources anymore.

A couple of important, doc-confirmed specifics baked in below:
  - Engine hours is NOT nested under the org. It's a top-level endpoint:
        GET /platform/machines/{machineId}/engineHours
  - Per-machine resources (location history, hours of operation, alerts,
    device state reports) are expected to be linked off each MACHINE's own
    `links` array (same HATEOAS pattern as the org), not the org's. The
    exact `rel` name for each can vary by sandbox account, so
    get_machine_related() is tried against a short list of likely
    candidates — see app_jd.py's "Links available on this machine" panel
    to find the real rel name if the built-in guesses come up empty.
  - ISO 15143-3 (AEMP 2.0) is a separate, org-level, XML endpoint:
        GET /aemp/Fleet/{orgId}
    It's on your approved list and doesn't depend on any guessed rel name,
    so treat it as the most reliable "ground truth" data source here.

Setup:
    pip install flask requests python-dotenv

.env file should contain:
    JOHN_DEERE_CLIENT_ID=...
    JOHN_DEERE_CLIENT_SECRET=...
    JOHN_DEERE_REDIRECT_URI=http://localhost:9090/callback
    JOHN_DEERE_ENV=production   # or "sandbox" — see note near BASE_URL below

Run once to connect (opens a browser for login):
    python johndeere.py

After that, other scripts (like app_jd.py) can just import this module and
call get_valid_access_token() — it reuses the saved token automatically.
"""

import os
import json
import secrets
import webbrowser
import xml.etree.ElementTree as ET

import requests

from urllib.parse import urlencode
from dotenv import load_dotenv
from flask import Flask, request

load_dotenv()

CLIENT_ID = os.getenv("JOHN_DEERE_CLIENT_ID")
CLIENT_SECRET = os.getenv("JOHN_DEERE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("JOHN_DEERE_REDIRECT_URI")

# "sandbox" = JD's fake test organizations (sandboxapi.deere.com) — no real
# org/machine data, works for any registered developer with zero approval.
# "production" = your real Operations Center org (api.deere.com) — this is
# what you actually want if you're seeing your real "AgroIntel" org with
# real Equipment/Locations/Financial/Work consent toggles on connections.deere.com.
# Set JOHN_DEERE_ENV=production in your .env once you've granted org consent.
JOHN_DEERE_ENV = os.getenv("JOHN_DEERE_ENV", "production").strip().lower()
IS_PRODUCTION = JOHN_DEERE_ENV == "production"

AUTH_URL = "https://signin.johndeere.com/oauth2/aus78tnlaysMraFhC1t7/v1/authorize"
TOKEN_URL = "https://signin.johndeere.com/oauth2/aus78tnlaysMraFhC1t7/v1/token"
BASE_URL = "https://api.deere.com/platform" if IS_PRODUCTION else "https://sandboxapi.deere.com/platform"
AEMP_BASE_URL = "https://api.deere.com/aemp" if IS_PRODUCTION else "https://sandboxapi.deere.com/aemp"

TOKEN_FILE = "tokens.json"

# Trimmed to match what's actually been approved (eq1/eq2 = equipment +
# machine data, org1/org2 = organizations). ag* (fields/farms/boundaries)
# and files were dropped since that access wasn't granted — requesting them
# just adds noise to the consent screen for scopes that won't return data.
# Put "ag1 ag2 ag3 files" back here if/when that access is granted.
SCOPES = "eq1 eq2 org1 org2 offline_access"

app = Flask(__name__)

STATE = None


# ---------------------------------------------------------------------------
# Token persistence
# ---------------------------------------------------------------------------

def save_tokens(token_data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)


def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return json.load(f)
    return None


# ---------------------------------------------------------------------------
# OAuth flow
# ---------------------------------------------------------------------------

def get_login_url():
    global STATE
    STATE = secrets.token_urlsafe(16)

    params = {
        "response_type": "code",
        "scope": SCOPES,
        "client_id": CLIENT_ID,
        "state": STATE,
        "redirect_uri": REDIRECT_URI,
    }

    return AUTH_URL + "?" + urlencode(params)


def exchange_code_for_token(code):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    response = requests.post(TOKEN_URL, data=data, timeout=15)
    print("Token response status:", response.status_code)
    response.raise_for_status()

    token_data = response.json()
    save_tokens(token_data)
    return token_data


def refresh_access_token(refresh_token):
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    response = requests.post(TOKEN_URL, data=data, timeout=15)
    print("Refresh response status:", response.status_code)
    response.raise_for_status()

    token_data = response.json()
    save_tokens(token_data)
    return token_data


def get_valid_access_token():
    """
    Try to reuse a saved token, refreshing it if possible.
    Returns None if the user still needs to go through the browser login flow.
    """
    tokens = load_tokens()
    if not tokens:
        return None

    access_token = tokens.get("access_token")
    if access_token and _token_still_works(access_token):
        return access_token

    refresh_token = tokens.get("refresh_token")
    if refresh_token:
        try:
            new_tokens = refresh_access_token(refresh_token)
            return new_tokens["access_token"]
        except requests.HTTPError as e:
            print("Refresh failed, will need full re-login:", e)

    return None


def _token_still_works(access_token):
    """Cheap check: call organizations endpoint, see if it's a 401."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.deere.axiom.v3+json",
    }
    try:
        response = requests.get(f"{BASE_URL}/organizations", headers=headers, timeout=10)
        return response.status_code != 401
    except requests.RequestException:
        return False


# ---------------------------------------------------------------------------
# Core API calls
# ---------------------------------------------------------------------------

def _headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.deere.axiom.v3+json",
    }


def get_organizations(access_token):
    response = requests.get(f"{BASE_URL}/organizations", headers=_headers(access_token), timeout=15)
    print("Organizations response status:", response.status_code)
    response.raise_for_status()
    return response.json()


def fix_sandbox_host(url):
    """
    In SANDBOX mode, John Deere's sandbox organizations return `links`
    pointing at api.deere.com (production), even though sandbox access only
    works against sandboxapi.deere.com. Swap the host so every link
    actually hits the sandbox.

    In PRODUCTION mode this is a no-op — links returned by the production
    API already point at api.deere.com, which is exactly where they should
    go, so nothing needs rewriting.
    """
    if not url:
        return url
    if not IS_PRODUCTION and "api.deere.com" in url and "sandboxapi.deere.com" not in url:
        return url.replace("api.deere.com", "sandboxapi.deere.com")
    return url


def get_org_link(org, rel):
    """Pull a URL out of an organization's `links` list by its `rel` name."""
    for link in org.get("links", []):
        if link["rel"] == rel:
            return fix_sandbox_host(link["uri"])
    return None


def get_org_link_raw(org, rel):
    """Like get_org_link, but without the sandbox host rewrite (used for
    connections.deere.com links, which are not part of the platform API host)."""
    for link in org.get("links", []):
        if link["rel"] == rel:
            return link["uri"]
    return None


def get_manage_connection_url(org):
    return get_org_link_raw(org, "manage_connection")


def get_related(access_token, org, rel, params=None):
    """
    Generic fetch for anything linked off an ORGANIZATION. Kept for
    completeness / future access changes — app_jd.py no longer calls this
    for Fields/Farms/Boundaries/Assets/Files, since those aren't approved
    for this app registration and will just 403.
    """
    url = get_org_link(org, rel)
    if not url:
        print(f"No '{rel}' link found on this organization.")
        return None

    response = requests.get(url, headers=_headers(access_token), params=params, timeout=15)
    print(f"{rel} response status:", response.status_code)

    if response.status_code == 403:
        connect_url = get_manage_connection_url(org)
        print(f"\n--- Full 403 response body for '{rel}' ---")
        print(response.text)
        print("--- end response body ---\n")
        print(
            f"403 on '{rel}'. This is either a missing OAuth scope/license on your "
            f"app registration, or the data category hasn't been authorized for this "
            f"organization. The response body above should name the exact missing "
            f"scope/license. If it instead points at a connections link, open:\n"
            f"{connect_url}\n"
        )

    response.raise_for_status()
    return response.json()


def _extract_equipment_list(data):
    """
    Normalizes an equipment response into a plain list of machine dicts.
    The old /platform/organizations/{orgId}/machines endpoint wraps results
    in {"values": [...]}. The newer ISG gateway (api.deere.com/isg/equipment)
    may use a different envelope ("values", "content", or a bare list) — this
    just finds whichever shape is actually present instead of assuming one.
    """
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("values", "content", "equipment", "items"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def get_equipment(access_token, org_id, params=None, org=None):
    """
    Equipment is served via a HATEOAS link on the organization itself
    (rel='machines') — as of your account, that link points at John Deere's
    newer ISG gateway (api.deere.com/isg/equipment?organizationIds=...),
    NOT the old /platform/organizations/{orgId}/machines path. Following the
    org's own link (instead of hardcoding the old path) is what actually
    respects the consent you granted for this org.

    Falls back to the legacy hardcoded path only if no `org` dict is passed
    in (so old call sites without the org object don't break outright),
    but you should always pass `org` now.
    """
    url = get_org_link(org, "machines") if org is not None else None
    if not url:
        url = f"{BASE_URL}/organizations/{org_id}/machines"

    query = dict(params or {})
    response = requests.get(url, headers=_headers(access_token), params=query, timeout=15)
    print("Equipment response status:", response.status_code, "url:", url)

    if response.status_code in (403, 404):
        print(f"\n--- Full {response.status_code} response body for 'equipment' ---")
        print(response.text)
        print("--- end response body ---\n")
        if response.status_code == 403:
            detail = "This org hasn't granted your app consent for Equipment/machine data yet."
            connect_url = get_manage_connection_url(org) if org else None
            if connect_url:
                detail += f" Grant it here: {connect_url}"
            err = requests.HTTPError(detail, response=response)
            err.manage_connection_url = connect_url
            raise err

    response.raise_for_status()
    data = response.json()
    # Return in the same {"values": [...]} shape callers already expect,
    # regardless of which envelope the underlying host actually used.
    return {"values": _extract_equipment_list(data)}


def get_all_pages(access_token, url, params=None):
    """Follow `nextPage` links to collect every page of results."""
    all_values = []
    params = dict(params or {})
    params.setdefault("count", 100)

    while url:
        response = requests.get(url, headers=_headers(access_token), params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        all_values.extend(data.get("values", []))

        next_link = next(
            (l["uri"] for l in data.get("links", []) if l["rel"] == "nextPage"),
            None,
        )
        url = fix_sandbox_host(next_link)
        params = None  # nextPage URL already has query params baked in

    return all_values


# ---------------------------------------------------------------------------
# Per-MACHINE resources (Locations, Hours of Operation, Alerts, Device State)
# ---------------------------------------------------------------------------
#
# These are expected to be linked off each machine's own `links` array
# (the way `get_equipment()` returns them), the same HATEOAS pattern as
# organizations. The exact `rel` name for each resource can vary by sandbox
# account, so get_machine_related() below is tried against a short list of
# likely candidates for each resource type in app_jd.py. If none of the
# candidates hit, app_jd.py shows the machine's raw `links` array so you can
# read off the real rel name and add it to the candidate list.

def get_machine_link(machine, rel):
    """Pull a URL out of a machine's `links` list by its `rel` name."""
    for link in machine.get("links", []):
        if link["rel"] == rel:
            return fix_sandbox_host(link["uri"])
    return None


def get_machine_related(access_token, machine, rel, params=None):
    """
    Generic fetch for anything linked off a single MACHINE (locations,
    hours of operation, alerts, device state reports, etc). Returns None
    (rather than raising) when the rel isn't present or the call 403/404s,
    so callers can just try several candidate rel names in a loop.
    """
    url = get_machine_link(machine, rel)
    if not url:
        return None

    response = requests.get(url, headers=_headers(access_token), params=params, timeout=15)
    print(f"machine[{machine.get('id')}] '{rel}' response status:", response.status_code)

    if response.status_code in (403, 404):
        print(f"\n--- {response.status_code} body for machine rel '{rel}' ---")
        print(response.text[:1000])
        print("--- end response body ---\n")
        return None

    response.raise_for_status()
    return response.json()


def get_engine_hours(access_token, machine_id, last_known=False):
    """
    Confirmed, documented endpoint (not nested under the org):
        GET /platform/machines/{machineId}/engineHours?lastKnown={bool}
    """
    url = f"{BASE_URL}/machines/{machine_id}/engineHours"
    params = {"lastKnown": "true" if last_known else "false"}

    response = requests.get(url, headers=_headers(access_token), params=params, timeout=15)
    print(f"Engine hours (machine {machine_id}) response status:", response.status_code)

    if response.status_code in (403, 404):
        print(f"\n--- {response.status_code} body for engineHours ---")
        print(response.text[:1000])
        print("--- end response body ---\n")

    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# Map Layers (org-level, rel name unconfirmed — tries a short candidate list)
# ---------------------------------------------------------------------------

MAP_LAYER_REL_CANDIDATES = ["mapLayers", "mapLayerImages", "layers"]


def get_map_layers(access_token, org, params=None):
    """
    Best-effort fetch of Map Layers off the organization. Raises the last
    error encountered if every candidate rel fails, so the caller can show
    a clear "not available" message instead of silently returning nothing.
    """
    last_error = None
    for rel in MAP_LAYER_REL_CANDIDATES:
        url = get_org_link(org, rel)
        if not url:
            continue
        try:
            response = requests.get(url, headers=_headers(access_token), params=params, timeout=15)
            if response.status_code in (403, 404):
                last_error = f"'{rel}' -> HTTP {response.status_code}"
                continue
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            last_error = f"'{rel}' -> {e}"
            continue

    if last_error:
        connect_url = get_manage_connection_url(org)
        if connect_url:
            last_error += f" Grant consent here: {connect_url}"
        err = RuntimeError(last_error)
        err.manage_connection_url = connect_url
        raise err
    return None


# ---------------------------------------------------------------------------
# ISO 15143-3 (AEMP 2.0) Fleet snapshot — org-level, XML, on the approved list
# ---------------------------------------------------------------------------

def _strip_ns(tag):
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _xml_elem_to_dict(elem):
    """
    Converts an XML element into a plain dict (attributes + text + nested
    children), stripping namespaces. Schema fields reported by AEMP vary by
    machine/telematics capability, so this stays flexible instead of
    hardcoding a fixed set of expected fields — whatever a machine actually
    reports comes through as-is.
    """
    d = {}
    for k, v in elem.attrib.items():
        d[_strip_ns(k)] = v

    text = (elem.text or "").strip()
    if text:
        d["_text"] = text

    children_by_tag = {}
    for child in elem:
        tag = _strip_ns(child.tag)
        children_by_tag.setdefault(tag, []).append(_xml_elem_to_dict(child))

    for tag, items in children_by_tag.items():
        d[tag] = items if len(items) > 1 else items[0]

    return d


def get_aemp_fleet(access_token, org_id, max_pages=5, org=None):
    """
    ISO 15143-3 (AEMP 2.0) Fleet snapshot for an organization:
        GET /aemp/Fleet/{orgId}
    Cached on Deere's servers for an hour (per their docs) — no need to
    poll more often than that.

    Returns a list of flexible dicts, one per <Equipment> element in the
    response. Use summarize_aemp_equipment() to pull out the common fields
    for display, or inspect the raw dicts for anything else a machine
    reported (fuel, DEF, load count, distance, etc).
    """
    url = f"{AEMP_BASE_URL}/Fleet/{org_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.deere.axiom.v3+xml, application/xml;q=0.9, */*;q=0.5",
    }

    equipment_list = []
    pages = 0

    while url and pages < max_pages:
        response = requests.get(url, headers=headers, timeout=20)
        print("AEMP Fleet response status:", response.status_code)

        if response.status_code in (403, 404):
            print(f"\n--- {response.status_code} body for AEMP Fleet ---")
            print(response.text[:2000])
            print("--- end response body ---\n")
            if response.status_code == 403:
                detail = "This org hasn't granted your app consent for ISO 15143-3 data yet."
                connect_url = get_manage_connection_url(org) if org else None
                if connect_url:
                    detail += f" Grant it here: {connect_url}"
                err = requests.HTTPError(detail, response=response)
                err.manage_connection_url = connect_url
                raise err

        response.raise_for_status()

        root = ET.fromstring(response.content)
        for elem in root.iter():
            if _strip_ns(elem.tag) == "Equipment":
                equipment_list.append(_xml_elem_to_dict(elem))

        next_url = None
        for link_elem in root.iter():
            if _strip_ns(link_elem.tag) != "Link":
                continue
            rel, href = None, None
            for child in link_elem:
                ctag = _strip_ns(child.tag)
                if ctag == "rel":
                    rel = (child.text or "").strip()
                elif ctag == "href":
                    href = (child.text or "").strip()
            if rel == "next" and href:
                next_url = href

        url = next_url
        pages += 1

    return equipment_list


def summarize_aemp_equipment(equip):
    """
    Best-effort extraction of the fields most useful for display out of the
    flexible AEMP dict. Returns '—'-friendly None values when a machine
    hasn't reported something — not every machine supports every field.
    """
    header = equip.get("Header", {})
    if isinstance(header, list):
        header = header[0] if header else {}

    locations = equip.get("Locations") or equip.get("Location")
    last_location = None
    if locations:
        loc_list = locations.get("Location") if isinstance(locations, dict) else locations
        if isinstance(loc_list, dict):
            loc_list = [loc_list]
        if loc_list:
            last_location = loc_list[-1]

    hours = None
    for key in equip.keys():
        if "Hour" in key:
            val = equip[key]
            if isinstance(val, list):
                val = val[-1]
            hours = val
            break

    return {
        "make": header.get("make") or header.get("Make"),
        "model": header.get("model") or header.get("Model"),
        "vin": header.get("equipmentVIN") or header.get("serialNumber") or header.get("machineId"),
        "location": last_location,
        "hours": hours,
    }


# ---------------------------------------------------------------------------
# Flask OAuth callback
# ---------------------------------------------------------------------------

@app.route("/callback")
def callback():
    code = request.args.get("code")
    returned_state = request.args.get("state")
    error = request.args.get("error")

    if error:
        return f"John Deere authorization failed: {error}"

    if not code:
        return "No authorization code received."

    if returned_state != STATE:
        return "State mismatch. Possible OAuth security issue."

    print("\nAuthorization code received!")

    try:
        token_data = exchange_code_for_token(code)
        access_token = token_data["access_token"]

        print("\n=== ACCESS TOKEN RECEIVED ===")
        print("(saved to tokens.json)")

        orgs = get_organizations(access_token)
        print("\n=== ORGANIZATIONS ===")
        print(orgs)

        if orgs.get("values"):
            org = orgs["values"][0]

            equipment = get_equipment(access_token, org["id"], org=org)
            print("\n=== EQUIPMENT ===")
            print(equipment)

        return """
        <h2>John Deere API Connected Successfully! 🚜</h2>
        <p>Authorization successful. Tokens saved to tokens.json.</p>
        <p>Check your Python terminal for organizations and equipment.</p>
        <p>You can close this tab. Your dashboard (app_jd.py) will now be able to
        reuse this same token automatically — no need to log in again there.</p>
        """

    except Exception as e:
        print("\nERROR:", e)
        return f"Error while connecting to John Deere API: {e}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    access_token = get_valid_access_token()

    if access_token:
        print("\nReusing saved/refreshed access token — no browser login needed.")
        orgs = get_organizations(access_token)
        print("\n=== ORGANIZATIONS ===")
        print(orgs)

        if orgs.get("values"):
            org = orgs["values"][0]
            equipment = get_equipment(access_token, org["id"], org=org)
            print("\n=== EQUIPMENT ===")
            print(equipment)
        return

    login_url = get_login_url()

    print("\n=== JOHN DEERE OAUTH ===")
    print("\nOpen this URL in your browser:\n")
    print(login_url)
    print("\nWaiting for John Deere callback...")
    print("Listening on http://localhost:9090/callback")

    try:
        webbrowser.open(login_url)
    except Exception:
        pass

    app.run(port=9090)


if __name__ == "__main__":
    main()