"""
printify_desk.py

First job: prove the connection to Printify actually works, and find your
shop automatically so you never have to hunt for a numeric Shop ID.
"""

import os
import requests

API_BASE = "https://api.printify.com/v1"


def _headers():
    token = os.environ.get("PRINTIFY_API_TOKEN")
    if not token:
        raise RuntimeError("PRINTIFY_API_TOKEN is not set in the environment.")
    return {"Authorization": f"Bearer {token}"}


def test_connection() -> str:
    resp = requests.get(f"{API_BASE}/shops.json", headers=_headers(), timeout=15)
    if resp.status_code != 200:
        return f"Connection failed ({resp.status_code}): {resp.text[:200]}"

    shops = resp.json()
    if not shops:
        return "Connected, but no shops found on this Printify account."

    lines = [f"Connected. Found {len(shops)} shop(s):"]
    for shop in shops:
        lines.append(f"  - {shop['title']} (id: {shop['id']}, platform: {shop['sales_channel']})")
    return "\n".join(lines)
