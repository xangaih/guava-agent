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
    "raise_budget": "caller agrees to raise their total trip budget to afford something",
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


_STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "for", "of", "in", "on", "at", "with",
    "please", "add", "confirm", "remove", "drop", "swap", "switch", "let", "lets",
    "trip", "itinerary", "plan", "proceed", "that", "this", "it", "my", "our",
    "we", "i", "want", "would", "like", "some", "any", "hotel", "restaurant",
    "experience", "option", "options", "also", "just", "go", "do", "done",
}


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower())) - _STOPWORDS


def _find_item(trip_id: str, request_text: str, statuses=("proposed",)):
    import json
    import sqlite3

    conn = sqlite3.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row
    items = [dict(r) for r in conn.execute(
        f"SELECT * FROM itinerary_items WHERE trip_id = ? AND status IN ({','.join('?' * len(statuses))})",
        (trip_id, *statuses),
    ).fetchall()]

    request_lower = (request_text or "").lower()
    request_words = _words(request_text)

    # Exact-title substring match is the strongest signal (handles short,
    # single-word names like "Kikunoi" that word-overlap scoring alone can't
    # distinguish from ambient noise).
    for item in items:
        if item["title"].lower() in request_lower:
            conn.close()
            return item

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
    return best_item if best_score >= 2 else None


def _attempt_confirm(call: guava.Call, trip_id: str, item: dict) -> bool:
    """Try to confirm `item`. Returns True if confirmed, False if a tradeoff was offered instead."""
    already_confirmed_cost = sum(
        i["cost"] or 0 for i in db.list_itinerary_items(trip_id, status="confirmed")
    )
    trip = db.get_trip(trip_id)
    remaining_after_confirm = trip["total_budget"] - (already_confirmed_cost + item["cost"])

    if remaining_after_confirm >= 0:
        db.update_itinerary_item(item["id"], status="confirmed")
        call.set_variable("pending_tradeoff", None)
        call.send_instruction(f"Confirm that {item['title']} has been added to their trip.")
        return True

    over_amount = -remaining_after_confirm
    tradeoffs = budget.generate_tradeoffs(trip_id, item, over_amount)
    call.set_variable("pending_tradeoff", {"item_id": item["id"], "over_amount": over_amount})
    call.send_instruction(
        f"Explain that confirming {item['title']} (${item['cost']:.0f}) would put the trip "
        f"${over_amount:.0f} over budget. Mention just one of these options at a time, weighing "
        f"both what it saves and what it does to the flow of the trip (extra travel between "
        f"stops, a day that no longer overlaps, etc.) rather than leading with price — and "
        f"recommend the one that best fits their stated spend priorities: {tradeoffs}"
    )
    return False


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

    _attempt_confirm(call, trip_id, item)


@agent.on_action("remove_from_itinerary")
def on_remove_from_itinerary(call: guava.Call):
    trip_id = call.get_variable("trip_id")
    request_text = call.get_variable("last_request", "")
    item = _find_item(trip_id, request_text, statuses=("proposed", "confirmed"))

    if not item:
        call.send_instruction("Ask the caller to clarify which item they want to remove.")
        return

    db.update_itinerary_item(item["id"], status="removed")

    pending = call.get_variable("pending_tradeoff")
    if pending and pending["item_id"] != item["id"]:
        pending_item = next(
            (i for i in db.list_itinerary_items(trip_id) if i["id"] == pending["item_id"]), None
        )
        if pending_item:
            confirmed = _attempt_confirm(call, trip_id, pending_item)
            if confirmed:
                call.send_instruction(
                    f"Confirm that {item['title']} was removed and, with that freed-up budget, "
                    f"{pending_item['title']} has now been added to their trip."
                )
                return

    call.send_instruction(f"Confirm that {item['title']} has been removed from their trip.")


@agent.on_action("raise_budget")
def on_raise_budget(call: guava.Call):
    trip_id = call.get_variable("trip_id")
    pending = call.get_variable("pending_tradeoff")
    if not pending:
        call.send_instruction("Let the caller know there's nothing pending to raise the budget for.")
        return

    trip = db.get_trip(trip_id)
    over_amount = pending["over_amount"]
    new_budget = trip["total_budget"] + over_amount

    import sqlite3
    conn = sqlite3.connect(db.DB_PATH)
    conn.execute("UPDATE trips SET total_budget = ? WHERE id = ?", (new_budget, trip_id))
    conn.commit()
    conn.close()

    db.insert_constraint_override(
        trip_id=trip_id,
        constraint_name="total_budget",
        profile_value=str(trip["total_budget"]),
        override_value=str(new_budget),
        scope="trip",
        reason="caller agreed to raise budget to afford a proposed item",
    )

    pending_item = next(
        (i for i in db.list_itinerary_items(trip_id) if i["id"] == pending["item_id"]), None
    )
    if pending_item:
        db.update_itinerary_item(pending_item["id"], status="confirmed")
        call.set_variable("pending_tradeoff", None)
        call.send_instruction(
            f"Confirm the budget has been raised to ${new_budget:.0f} and {pending_item['title']} "
            "has been added to their trip."
        )


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


_CITY_RECAP_IMAGES = {
    "kyoto": "/assets/kyoto.png",
    "paris": "/assets/paris.png",
}


def finalize_trip(call: guava.Call, closing_note: str = "Thank them and say their trip is ready to view."):
    """Mark the trip finalized, recap it, and end the call. Shared by the explicit
    'finalize_trip' intent and the trip_planning task's completion criteria, so the
    call ends the same way whether the caller asks to wrap up or just runs out of asks."""
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

    city = (trip["destination"] or "").split(",")[0].strip().lower()
    recap_image = _CITY_RECAP_IMAGES.get(city)
    if recap_image:
        db.insert_trip_comic(trip_id, recap_image)

    call.send_instruction(
        "Give a short, warm recap of the finalized trip and let them know their plan is ready "
        f"on screen. Total confirmed spend: ${total_cost:.0f} of ${trip['total_budget']:.0f}."
        + ("" if within_budget else " Note the trip is slightly over budget.")
    )
    call.hangup(final_instructions=closing_note)


@agent.on_action("finalize_trip")
def on_finalize_trip(call: guava.Call):
    finalize_trip(call)


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
