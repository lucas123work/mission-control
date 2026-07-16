"""
office_state.py

Single shared state file that every desk/agent script reads from and writes to.
This is intentionally a plain JSON file, not a database — the whole point of
this hub is that one human can open state.json, or the dashboard, and see the
truth about what is and isn't actually running.

Any future script (printify_desk.py, ebay_flip_finder.py, etc.) should only
need two calls to hook into the hub:

    from office_state import set_output, get_room

    get_room("printify_desk")["status"]   # check before doing anything that publishes
    set_output("printify_desk", "Uploaded 3 designs, awaiting review", status="awaiting_review")
"""

import json
import os
import threading
from datetime import datetime, timezone

STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")
_lock = threading.Lock()

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


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _load() -> dict:
    with open(STATE_PATH, "r") as f:
        return json.load(f)


def _save(state: dict) -> None:
    tmp_path = STATE_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp_path, STATE_PATH)


def get_state() -> dict:
    with _lock:
        return _load()


def get_room(agent_id: str) -> dict | None:
    state = get_state()
    return state["agents"].get(agent_id)


def log_event(text: str) -> None:
    with _lock:
        state = _load()
        state["log"].append({"ts": _now(), "text": text})
        state["log"] = state["log"][-50:]  # keep it short, this is a log not an archive
        _save(state)


def set_output(agent_id: str, output: str, status: str | None = None) -> None:
    """Any pipeline script calls this after doing work, so the hub reflects reality."""
    with _lock:
        state = _load()
        if agent_id not in state["agents"]:
            raise KeyError(f"Unknown agent '{agent_id}' — add it to state.json first.")
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
            raise KeyError(f"Unknown agent '{agent_id}' — add it to state.json first.")
        state["agents"][agent_id]["status"] = status
        _save(state)


def update_notes(agent_id: str, notes: str) -> None:
    with _lock:
        state = _load()
        if agent_id not in state["agents"]:
            raise KeyError(f"Unknown agent '{agent_id}' — add it to state.json first.")
        state["agents"][agent_id]["notes"] = notes
        _save(state)


def update_finance(earned_delta: float = 0.0, spent_delta: float = 0.0, note: str = "") -> None:
    """
    Money in/out is logged manually right now, on purpose. Nothing in this
    project has a live payment webhook connected, so a manual entry point is
    the honest version rather than a fake live ticker.
    """
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
