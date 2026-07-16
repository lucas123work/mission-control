"""
office_state.py

Same job as before — every desk/agent script reads and writes through this
file — but the actual data now lives in Supabase (a free hosted database)
instead of a local file, so it survives restarts and redeploys.

Needs two environment variables set wherever this runs (set them in Render's
"Environment" tab, never commit them into the code):
    SUPABASE_URL
    SUPABASE_KEY   (the service_role key)
"""

import os
import threading
from datetime import datetime, timezone
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY must be set as environment variables "
        "(set these in Render's Environment tab, not in this file)."
    )

_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
_lock = threading.Lock()
ROW_ID = 1

VALID_STATUSES = {
    "not_started",
    "built_not_wired",
    "awaiting_setup",
    "awaiting_orders",
    "running",
    "awaiting_review",
    "approved",
    "blocked",
}

# Used only the very first time the app runs, to seed an empty database.
DEFAULT_STATE = {
    "finance": {"total_earned": 0.0, "total_spent": 0.0, "currency": "GBP"},
    "agents": {
        "idea_room": {
            "label": "Idea Room", "desk": "YouTube",
            "job": "Generates original video concepts",
            "status": "built_not_wired", "last_output": None,
            "notes": "Code exists (idea_room.py). Not yet reporting into this hub.",
        },
        "writers_room": {
            "label": "Writers' Room", "desk": "YouTube",
            "job": "Turns an idea into a full beat-by-beat script",
            "status": "built_not_wired", "last_output": None,
            "notes": "Code exists (writers_room.py). Not yet reporting into this hub.",
        },
        "voice_booth": {
            "label": "Voice Booth", "desk": "YouTube",
            "job": "Text-to-speech narration",
            "status": "not_started", "last_output": None,
            "notes": "Not built yet. Free TTS quality was flagged as a retention risk.",
        },
        "art_department": {
            "label": "Art Department", "desk": "YouTube",
            "job": "Illustrated panels for pan/zoom animation",
            "status": "not_started", "last_output": None,
            "notes": "Not built yet.",
        },
        "ebay_flip_finder": {
            "label": "eBay Flip Finder", "desk": "Reselling",
            "job": "Flags active-listing price gaps (Browse API, free tier)",
            "status": "not_started", "last_output": None,
            "notes": "v1 planned. Sold-price data needs a paid eBay Store + Terapeak later.",
        },
        "store_designer": {
            "label": "Store Designer", "desk": "Merch",
            "job": "AI-generates product names, descriptions and design concepts",
            "status": "not_started", "last_output": None,
            "notes": "Not built yet. Feeds straight into Printify Desk once running.",
        },
        "printify_desk": {
            "label": "Printify Desk", "desk": "Merch",
            "job": "Uploads designs as products via the Printify API",
            "status": "not_started", "last_output": None,
            "notes": "Not built yet. Printify itself is free; per-item cost applies on sale.",
        },
        "storefront": {
            "label": "Storefront", "desk": "Merch",
            "job": "Printify's free built-in Pop-Up Store (no Shopify needed)",
            "status": "not_started", "last_output": None,
            "notes": "Free. Revisit Shopify only once real sales justify ~£20+/mo.",
        },
        "tiktok_ads": {
            "label": "TikTok Ads", "desk": "Marketing",
            "job": "Posts/ad creative for the storefront",
            "status": "not_started", "last_output": None,
            "notes": "Blocked on TikTok developer app approval + business verification, not just code.",
        },
    },
    "log": [{"ts": "hub created", "text": "Mission Control initialised. All desks start honest: nothing runs unattended yet."}],
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _load() -> dict:
    res = _client.table("hub_state").select("data").eq("id", ROW_ID).execute()
    if res.data:
        return res.data[0]["data"]
    # First ever run: seed the database with the default board.
    _client.table("hub_state").insert({"id": ROW_ID, "data": DEFAULT_STATE}).execute()
    return DEFAULT_STATE


def _save(state: dict) -> None:
    _client.table("hub_state").upsert({"id": ROW_ID, "data": state}).execute()


def get_state() -> dict:
    with _lock:
        return _load()


def get_room(agent_id: str):
    state = get_state()
    return state["agents"].get(agent_id)


def log_event(text: str) -> None:
    with _lock:
        state = _load()
        state["log"].append({"ts": _now(), "text": text})
        state["log"] = state["log"][-50:]
        _save(state)


def set_output(agent_id: str, output: str, status: str = None) -> None:
    with _lock:
        state = _load()
        if agent_id not in state["agents"]:
            raise KeyError(f"Unknown agent '{agent_id}' — add it to DEFAULT_STATE first.")
        state["agents"][agent_id]["last_output"] = output
        if status:
            if status not in VALID_STATUSES:
                raise ValueError(f"Unknown status '{status}'. Use one of {VALID_STATUSES}")
            state["agents"][agent_id]["status"] = status
        state["log"].append({"ts": _now(), "text": f"{agent_id}: {output}"})
        state["log"] = state["log"][-50:]
        _save(state)


def set_status(agent_id: str, status: str) -> None:
    if status not in VALID_STATUSES:
        raise ValueError(f"Unknown status '{status}'. Use one of {VALID_STATUSES}")
    with _lock:
        state = _load()
        if agent_id not in state["agents"]:
            raise KeyError(f"Unknown agent '{agent_id}' — add it to DEFAULT_STATE first.")
        state["agents"][agent_id]["status"] = status
        _save(state)


def update_notes(agent_id: str, notes: str) -> None:
    with _lock:
        state = _load()
        if agent_id not in state["agents"]:
            raise KeyError(f"Unknown agent '{agent_id}' — add it to DEFAULT_STATE first.")
        state["agents"][agent_id]["notes"] = notes
        _save(state)


def update_finance(earned_delta: float = 0.0, spent_delta: float = 0.0, note: str = "") -> None:
    with _lock:
        state = _load()
        state["finance"]["total_earned"] += earned_delta
        state["finance"]["total_spent"] += spent_delta
        parts = []
        if earned_delta:
            parts.append(f"+£{earned_delta:.2f} earned")
        if spent_delta:
            parts.append(f"+£{spent_delta:.2f} spent")
        text = " / ".join(parts) if parts else "finance updated"
        if note:
            text += f" — {note}"
        state["log"].append({"ts": _now(), "text": text})
        state["log"] = state["log"][-50:]
        _save(state)
