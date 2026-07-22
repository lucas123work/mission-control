from flask import Flask, render_template, request, redirect, url_for
import office_state as store

app = Flask(__name__)

STATUS_META = {
    "not_started":     {"label": "Not started",     "tone": "muted"},
    "built_not_wired": {"label": "Built, not wired", "tone": "amber"},
    "awaiting_setup":  {"label": "Awaiting setup",   "tone": "amber"},
    "awaiting_orders": {"label": "Awaiting orders",  "tone": "amber"},
    "running":         {"label": "Running",          "tone": "teal"},
    "awaiting_review": {"label": "Awaiting your review", "tone": "amber"},
    "approved":        {"label": "Approved",         "tone": "teal"},
    "blocked":         {"label": "Blocked",          "tone": "rust"},
}


@app.route("/")
def index():
    state = store.get_state()
    agents = []
    for agent_id, agent in state["agents"].items():
        meta = STATUS_META.get(agent["status"], {"label": agent["status"], "tone": "muted"})
        agents.append({"id": agent_id, **agent, "status_label": meta["label"], "tone": meta["tone"]})

    net = state["finance"]["total_earned"] - state["finance"]["total_spent"]
    needs_review = sum(1 for a in agents if a["status"] == "awaiting_review")
    blocked = sum(1 for a in agents if a["status"] == "blocked")

    return render_template(
        "index.html",
        agents=agents,
        finance=state["finance"],
        net=net,
        needs_review=needs_review,
        blocked=blocked,
        log=list(reversed(state["log"][-20:])),
    )


@app.route("/approve/<agent_id>", methods=["POST"])
def approve(agent_id):
    store.set_status(agent_id, "approved")
    store.log_event(f"{agent_id}: approved by you")
    return redirect(url_for("index"))


@app.route("/note/<agent_id>", methods=["POST"])
def note(agent_id):
    text = request.form.get("notes", "")
    store.update_notes(agent_id, text)
    return redirect(url_for("index"))


@app.route("/finance", methods=["POST"])
def finance():
    def to_float(val):
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0.0

    earned = to_float(request.form.get("earned"))
    spent = to_float(request.form.get("spent"))
    note_text = request.form.get("note", "")
    store.update_finance(earned_delta=earned, spent_delta=spent, note=note_text)
    return redirect(url_for("index"))


@app.route("/run/printify_desk", methods=["POST"])
def run_printify_desk():
    import printify_desk
    try:
        result = printify_desk.test_connection()
        store.set_output("printify_desk", result, status="awaiting_orders")
    except Exception as e:
        store.set_output("printify_desk", f"Error: {e}", status="blocked")
    return redirect(url_for("index"))


@app.route("/run/printify_lookup", methods=["POST"])
def run_printify_lookup():
    import printify_desk
    try:
        result = printify_desk.find_tee_blueprint()
        store.set_output("printify_desk", result)
    except Exception as e:
        store.set_output("printify_desk", f"Error: {e}", status="blocked")
    return redirect(url_for("index"))


@app.route("/run/printify_providers", methods=["POST"])
def run_printify_providers():
    import printify_desk
    try:
        result = printify_desk.find_print_provider()
        store.set_output("printify_desk", result)
    except Exception as e:
        store.set_output("printify_desk", f"Error: {e}", status="blocked")
    return redirect(url_for("index"))


@app.route("/run/printify_variants", methods=["POST"])
def run_printify_variants():
    import printify_desk
    try:
        result = printify_desk.find_variants()
        store.set_output("printify_desk", result)
    except Exception as e:
        store.set_output("printify_desk", f"Error: {e}", status="blocked")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5050)
