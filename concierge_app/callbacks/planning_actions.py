import logging
import re

import guava
from guava import SuggestedAction
from guava.helpers.llm import IntentRecognizer

from concierge_app import db, voice_styles
from concierge_app.agent import agent
from concierge_app.specialists import budget

logger = logging.getLogger("concierge.planning_actions")

ACTIONS = {
    "add_to_itinerary": "caller wants to confirm or add a proposed hotel/restaurant/experience to the trip",
    "remove_from_itinerary": "caller wants to remove or swap something already planned",
    "budget_status": "caller is asking how much they've spent or have left in their budget",
    "finalize_trip": "caller is done planning and wants to wrap up the trip",
    "change_voice_style": (
        "caller is commenting on how the agent sounds or asking it to talk differently - "
        "more casual, more chill, calmer, slower, more professional, less slang, "
        "or naming a style directly"
    ),
}
intent_recognizer = IntentRecognizer(ACTIONS)


@agent.on_action_request
def on_action_request(call: guava.Call, request: str) -> list[SuggestedAction] | None:
    logger.info("Action request received: %s", request)
    call.set_variable("last_request", request)
    return intent_recognizer.classify(request)


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _find_item(trip_id: str, request_text: str, statuses=("proposed",)):
    import json
    import sqlite3

    conn = sqlite3.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row
    items = [dict(r) for r in conn.execute(
        f"SELECT * FROM itinerary_items WHERE trip_id = ? AND status IN ({','.join('?' * len(statuses))})",
        (trip_id, *statuses),
    ).fetchall()]

    request_words = _words(request_text)
    best_item, best_score = None, 0
    for item in items:
        blob_words = _words(item["title"]) | _words(item.get("location", ""))
        table = {"hotel": "hotels", "restaurant": "restaurants", "experience": "experiences"}.get(item["item_type"])
        if table and item["ref_id"]:
            row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (item["ref_id"],)).fetchone()
            if row:
                extra = dict(row)
                blob_words |= _words(extra.get("cuisine", ""))
                blob_words |= _words(" ".join(json.loads(extra.get("tags") or "[]")))
        score = len(blob_words & request_words)
        if score > best_score:
            best_item, best_score = item, score
    conn.close()
    return best_item if best_score > 0 else None


@agent.on_action("add_to_itinerary")
def on_add_to_itinerary(call: guava.Call):
    trip_id = call.get_variable("trip_id")
    request_text = call.get_variable("last_request", "")
    item = _find_item(trip_id, request_text, statuses=("proposed",))

    if not item:
        call.send_instruction(
            "Ask the caller to clarify which specific hotel, restaurant, or experience they mean."
        )
        return

    already_confirmed_cost = sum(
        i["cost"] or 0 for i in db.list_itinerary_items(trip_id, status="confirmed")
    )
    trip = db.get_trip(trip_id)
    remaining_after_confirm = trip["total_budget"] - (already_confirmed_cost + item["cost"])

    if remaining_after_confirm >= 0:
        db.update_itinerary_item(item["id"], status="confirmed")
        call.send_instruction(f"Confirm that {item['title']} has been added to their trip.")
        return

    over_amount = -remaining_after_confirm
    tradeoffs = budget.generate_tradeoffs(trip_id, item, over_amount)
    call.set_variable("pending_tradeoff_item_id", item["id"])
    call.send_instruction(
        f"Explain that confirming {item['title']} (${item['cost']:.0f}) would put the trip "
        f"${over_amount:.0f} over budget, then offer these specific options naturally and "
        f"recommend one based on their stated spend priorities: {tradeoffs}"
    )


@agent.on_action("remove_from_itinerary")
def on_remove_from_itinerary(call: guava.Call):
    trip_id = call.get_variable("trip_id")
    request_text = call.get_variable("last_request", "")
    item = _find_item(trip_id, request_text, statuses=("proposed", "confirmed"))

    if not item:
        call.send_instruction("Ask the caller to clarify which item they want to remove.")
        return

    db.update_itinerary_item(item["id"], status="removed")
    call.send_instruction(f"Confirm that {item['title']} has been removed from their trip.")


@agent.on_action("budget_status")
def on_budget_status(call: guava.Call):
    trip_id = call.get_variable("trip_id")
    trip = db.get_trip(trip_id)
    spent = budget.committed_and_proposed_total(trip_id)
    remaining = trip["total_budget"] - spent
    call.send_instruction(
        f"Tell the caller they've allocated ${spent:.0f} of their ${trip['total_budget']:.0f} "
        f"budget, with ${remaining:.0f} remaining."
    )


@agent.on_action("finalize_trip")
def on_finalize_trip(call: guava.Call):
    trip_id = call.get_variable("trip_id")
    items = db.list_itinerary_items(trip_id, status="confirmed")
    total_cost = sum(i["cost"] or 0 for i in items)
    trip = db.get_trip(trip_id)

    within_budget = total_cost <= (trip["total_budget"] or 0)
    import sqlite3
    conn = sqlite3.connect(db.DB_PATH)
    conn.execute("UPDATE trips SET status = 'finalized' WHERE id = ?", (trip_id,))
    conn.commit()
    conn.close()

    call.send_instruction(
        "Give a short, warm recap of the finalized trip and let them know their plan is ready "
        f"on screen. Total confirmed spend: ${total_cost:.0f} of ${trip['total_budget']:.0f}."
        + ("" if within_budget else " Note the trip is slightly over budget.")
    )
    call.hangup(final_instructions="Thank them and say their trip is ready to view.")


@agent.on_action("change_voice_style")
def on_change_voice_style(call: guava.Call):
    from concierge_app.callbacks.voice_style import switch_style

    request = call.get_variable("last_request") or ""
    style = switch_style(call, _style_from_request(request))
    call.send_instruction(
        f"Switch to a {style.label} manner starting now. Briefly acknowledge the change in that "
        "new manner, then pick the trip conversation back up exactly where it left off."
    )


_STYLE_CUES = {
    "genz": ("chill", "casual", "fun", "relaxed", "friend", "young", "girl", "slang", "loose",
             "genz", "zoomer", "texting", "vibe", "excited"),
    "steady": ("calm", "slow", "slower", "clearer", "clear", "professional", "serious", "formal",
               "plain", "straight", "older", "business", "repeat", "again", "hear", "understand",
               "confusing", "fast"),
    "friendly": ("friendly", "normal", "regular", "warm", "everyday", "neutral"),
}


def _style_from_request(request: str) -> str | None:
    """Best-effort mapping of 'talk more X' to a style key; falls back to the default."""
    words = _words(request)
    scores = {key: len(words & set(cues)) for key, cues in _STYLE_CUES.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else None
