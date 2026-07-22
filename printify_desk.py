"""
printify_desk.py

Handles all communication with the Printify API.
"""

import os
import io
import base64
import requests
from PIL import Image, ImageDraw, ImageFont

API_BASE = "https://api.printify.com/v1"
SHOP_ID = 28263870        # Tee Store Infinite — confirmed
TEE_BLUEPRINT_ID = 6      # Unisex Heavy Cotton Tee — confirmed
TEE_PROVIDER_ID = 410     # Printful — confirmed
TEST_VARIANT_IDS = [11848, 11849, 11850, 11851, 11852, 11853]  # Ash, sizes S-3XL


def _headers(json_body=True):
    token = os.environ.get("PRINTIFY_API_TOKEN")
    if not token:
        raise RuntimeError("PRINTIFY_API_TOKEN is not set in the environment.")
    h = {"Authorization": f"Bearer {token}"}
    if json_body:
        h["Content-Type"] = "application/json"
    return h


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


def find_print_provider() -> str:
    resp = requests.get(
        f"{API_BASE}/catalog/blueprints/{TEE_BLUEPRINT_ID}/print_providers.json",
        headers=_headers(), timeout=20,
    )
    if resp.status_code != 200:
        return f"Provider lookup failed ({resp.status_code}): {resp.text[:200]}"
    providers = resp.json()
    if not providers:
        return "No print providers found for this blueprint."
    lines = ["Available print providers:"]
    for p in providers[:5]:
        lines.append(f"  - {p['title']} (id: {p['id']})")
    return "\n".join(lines)


def find_variants() -> str:
    resp = requests.get(
        f"{API_BASE}/catalog/blueprints/{TEE_BLUEPRINT_ID}/print_providers/{TEE_PROVIDER_ID}/variants.json",
        headers=_headers(), timeout=20,
    )
    if resp.status_code != 200:
        return f"Variant lookup failed ({resp.status_code}): {resp.text[:200]}"
    data = resp.json()
    variants = data.get("variants", [])
    if not variants:
        return "No variants found."
    lines = [f"Found {len(variants)} variants. First 8:"]
    for v in variants[:8]:
        lines.append(f"  - {v['title']} (variant_id: {v['id']})")
    return "\n".join(lines)


def _make_placeholder_design() -> bytes:
    """Generates a simple text-based PNG so we have something real to upload."""
    img = Image.new("RGBA", (1000, 1000), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    text = "SAMPLE\nDESIGN"
    font = ImageFont.load_default()
    bbox = draw.multiline_textbbox((0, 0), text, font=font, align="center")
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.multiline_text(
        ((1000 - w) / 2, (1000 - h) / 2), text,
        fill=(20, 20, 20, 255), font=font, align="center",
    )
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_test_product() -> str:
    """
    Uploads a placeholder design and creates ONE draft product on Printify.
    Drafts are never published automatically — this only proves the pipeline
    works end-to-end. Safe to run, safe to delete afterward in Printify.
    """
    image_bytes = _make_placeholder_design()
    b64 = base64.b64encode(image_bytes).decode("utf-8")

    upload_resp = requests.post(
        f"{API_BASE}/uploads/images.json",
        headers=_headers(),
        json={"file_name": "sample_design.png", "contents": b64},
        timeout=30,
    )
    if upload_resp.status_code != 200:
        return f"Image upload failed ({upload_resp.status_code}): {upload_resp.text[:300]}"
    image_id = upload_resp.json()["id"]

    product_body = {
        "title": "Sample Test Tee — DO NOT PUBLISH",
        "description": (
            "Internal test product created by Mission Control to confirm the "
            "Printify pipeline works end-to-end. Safe to delete."
        ),
        "blueprint_id": TEE_BLUEPRINT_ID,
        "print_provider_id": TEE_PROVIDER_ID,
        "variants": [{"id": vid, "price": 2000, "is_enabled": True} for vid in TEST_VARIANT_IDS],
        "print_areas": [
            {
                "variant_ids": TEST_VARIANT_IDS,
                "placeholders": [
                    {"position": "front", "images": [{"id": image_id, "x": 0.5, "y": 0.5, "scale": 1, "angle": 0}]}
                ],
            }
        ],
    }

    product_resp = requests.post(
        f"{API_BASE}/shops/{SHOP_ID}/products.json",
        headers=_headers(),
        json=product_body,
        timeout=30,
    )
    if product_resp.status_code not in (200, 201):
        return f"Product creation failed ({product_resp.status_code}): {product_resp.text[:300]}"

    product = product_resp.json()
    return (
        f"Draft product created: '{product['title']}' (product_id: {product['id']}).\n"
        f"This is a DRAFT only — nothing published, nothing for sale.\n"
        f"Go check it in your Printify dashboard under Products."
    )
