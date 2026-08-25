"""
RVO (Rijksdienst voor Ondernemend Nederland) Open Data Client
----------------------------------------------------------------
Fully open — no account, no API key, no OAuth. Plain GET requests.

Endpoints (50 results per page):
    subsidies  -> https://www.rvo.nl/api/v1/opendata/subsidies
    articles   -> https://www.rvo.nl/api/v1/opendata/articles     (nieuws)
    events     -> https://www.rvo.nl/api/v1/opendata/events
    showcases  -> https://www.rvo.nl/api/v1/opendata/showcases    (praktijkverhalen)
    subjects   -> https://www.rvo.nl/api/v1/opendata/subjects     (onderwerpen)
    blogs      -> https://www.rvo.nl/api/v1/opendata/blogs

We're pulling `subsidies`, since that's what's relevant for AgroIntel —
funding/grants for agricultural businesses — and filtering client-side
for the agricultural sector.

Run:
    pip install requests
    python rvo_client.py
"""

import requests

BASE_URL = "https://www.rvo.nl/api/v1/opendata"


def get_subsidies(page=None):
    """
    Fetch RVO subsidy/funding listings. No auth needed.
    page: optional page number (API returns 50 results per page).
    """
    url = f"{BASE_URL}/subsidies"
    params = {"page": page} if page is not None else None

    response = requests.get(url, params=params, timeout=30)
    print("RVO subsidies response status:", response.status_code)
    response.raise_for_status()

    return response.json()


def get_agri_subsidies(page=None):
    """
    Same as get_subsidies, filtered client-side to schemes relevant to
    agricultural businesses (sector 'Agrarische sector' or subject 'Landbouw').
    """
    all_items = get_subsidies(page)

    return [
        item for item in all_items
        if "Agrarische sector" in item.get("sectors", [])
        or "Landbouw" in item.get("subjects", [])
        or any("Agrarisch" in t for t in item.get("targets", []))
    ]


if __name__ == "__main__":
    agri = get_agri_subsidies()

    print(f"\n=== AGRICULTURAL SUBSIDIES ({len(agri)} found) ===")
    for item in agri[:10]:
        print(f"- {item['title']}")
        print(f"  {item['intro'][:120]}...")
        print(f"  https://www.rvo.nl{item['url']}")
        print()