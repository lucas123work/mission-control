"""
printify_desk.py

Handles all communication with the Printify API: confirming the connection
works, and looking up product blueprints to use later.
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


def find_tee_blueprint() -> str:
    resp = requests.get(f"{API_BASE}/catalog/blueprints.json", headers=_headers(), timeout=20)
    if resp.status_code != 200:
        return f"Blueprint lookup failed ({resp.status_code}): {resp.text[:200]}"

    blueprints = resp.json()
    matches = [b for b in blueprints if "heavy cotton tee" in b["title"].lower()]
    if not matches:
        matches = [b for b in blueprints if "t-shirt" in b["title"].lower()][:3]

    lines = ["Candidate blueprints:"]
    for b in matches[:3]:
        lines.append(f"  - {b['title']} (blueprint_id: {b['id']})")
    return "\n".join(lines)
