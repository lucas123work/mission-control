# Mission Control

This is the hub: one page that shows every desk/agent in the plan, its real
status, what it last did, and the actual money earned vs. spent so far. It
runs entirely on your machine — nothing is sent anywhere.

It intentionally starts **empty and honest**. Every desk shows
`not_started` or `built, not wired` until you or a script says otherwise.
There is no fake "running 24/7" ticker — that's the exact overselling this
project explicitly rejected.

## Run it

```bash
cd mission_control
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5050**

## What's in here

- `state.json` — the single source of truth. One JSON file, human-readable,
  safe to open and edit directly if you ever want to.
- `office_state.py` — the only file any future agent script needs to import.
  Three calls cover everything:

  ```python
  from office_state import get_room, set_output, update_finance

  # before doing anything that publishes or spends money:
  if get_room("printify_desk")["status"] == "approved":
      ...

  # after doing work:
  set_output("printify_desk", "Drafted 3 tee designs, waiting on your review",
             status="awaiting_review")

  # when a real sale happens:
  update_finance(earned_delta=12.50, note="Etsy: history t-shirt sale")
  ```

- `app.py` — the Flask server. Renders the page, handles the "Approve",
  "Save note", and "Log" (finance) buttons.
- `templates/index.html` + `static/style.css` — the page itself.

## The eight desks already on the board

These come straight from the handoff, not from the "runs businesses while I
sleep" screenshots — those were about someone else's agents and don't reflect
what's actually built here.

| Desk | Desk group | Real status |
|---|---|---|
| Idea Room | YouTube | code exists, not wired to this hub yet |
| Writers' Room | YouTube | code exists, not wired to this hub yet |
| Voice Booth | YouTube | not started |
| Art Department | YouTube | not started |
| eBay Flip Finder | Reselling | not started |
| Printify Desk | Merch | not started |
| Shopify Sync | Merch | not started |
| TikTok Ads | Marketing | not started (blocked on API approval, not code) |

## Adding a new desk later

Add an entry under `"agents"` in `state.json` with `label`, `desk`, `job`,
`status`, `last_output`, `notes` — then it shows up on the board automatically.
No other code changes needed.

## Human-review gate

Any desk whose status is `awaiting_review` gets an **Approve to publish**
button on its card, and nothing moves past that without you clicking it.
This isn't just a UI nicety — it's the thing standing between this project
and YouTube's 2026 policy that terminates channels for templated,
no-visible-human-direction content. Keep this gate in every future script,
even once Printify/Shopify/TikTok pieces are wired in.
