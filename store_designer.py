"""
store_designer.py

Generates original t-shirt concepts: a tagline (the actual design text),
a product title, and a short description. Free, template-based — no paid
AI API, no ongoing cost. Themed around the history-channel niche for
brand consistency with the YouTube side of this project.
"""

import random

ADJECTIVES = ["Certified", "Professional", "Certifiable", "Chronic", "Unapologetic", "Card-Carrying"]
SUBJECTS = ["History Nerd", "History Buff", "Primary Source Enjoyer", "Ancient History Addict",
            "Documentary Hoarder", "Footnote Reader"]

OPENERS = ["I'D RATHER BE READING ABOUT", "ASK ME ABOUT", "WARNING: WILL TALK ABOUT", "WORLD'S OKAYEST HISTORIAN ON"]
TOPICS = ["THE FALL OF ROME", "THE BRONZE AGE COLLAPSE", "MEDIEVAL PLAGUES", "THE SILK ROAD",
          "ANCIENT EGYPT", "THE VICTORIAN ERA", "LOST CIVILIZATIONS", "THE FRENCH REVOLUTION"]

DESCRIPTIONS = [
    "For the person who turns every conversation into a history lecture, on purpose.",
    "Because someone at this party needs to bring up an obscure historical fact unprompted.",
    "Soft cotton. Strong opinions about primary sources.",
    "Wear your niche interest where everyone can see it.",
]


def _make_tagline() -> str:
    style = random.choice(["adjective_subject", "opener_topic"])
    if style == "adjective_subject":
        return f"{random.choice(ADJECTIVES).upper()} {random.choice(SUBJECTS).upper()}"
    return f"{random.choice(OPENERS)} {random.choice(TOPICS)}"


def propose_product() -> dict:
    tagline = _make_tagline()
    title = f"{tagline.title()} — History Nerd Tee"
    description = random.choice(DESCRIPTIONS)
    return {"tagline": tagline, "title": title, "description": description}
