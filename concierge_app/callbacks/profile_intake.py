import logging

import guava

from concierge_app import db, status_store, voice_styles
from concierge_app.agent import agent
from concierge_app.callbacks.planning_actions import finalize_trip
from concierge_app.specialists import budget, experiences, hotels, restaurants

logger = logging.getLogger("concierge.profile_intake")


def start_trip_intake(call: guava.Call):
    call.set_task(
        "trip_intake",
        objective="Learn how this traveler likes to travel and get the shape of this trip.",
        checklist=[
            guava.Field(key="destination", field_type="text", description="Where they want to go"),
            guava.Field(key="trip_length_days", field_type="integer", description="How many days"),
            guava.Field(key="party_size", field_type="integer", description="How many people traveling"),
            guava.Field(key="total_budget", field_type="integer", description="Total trip budget in dollars"),
            guava.Field(
                key="pace", field_type="multiple_choice",
                choices=["relaxed", "balanced", "packed"],
                description="Relaxed wandering vs. see-everything pace",
            ),
            guava.Field(
                key="top_interests", field_type="text",
                description="What they most enjoy on trips — food, architecture, nightlife, etc.",
            ),
            guava.Field(
                key="spend_priorities", field_type="text",
                description="What they actually like spending money on vs. don't care about",
            ),
        ],
    )


@agent.on_task_complete("trip_intake")
def on_trip_intake_complete(call: guava.Call):
    destination = call.get_field("destination") or "Kyoto, Japan"
    total_budget = call.get_field("total_budget") or 3000
    pace = call.get_field("pace") or "balanced"
    top_interests_raw = call.get_field("top_interests") or ""
    spend_priorities = call.get_field("spend_priorities") or ""
    interests = [i.strip() for i in top_interests_raw.replace(" and ", ",").split(",") if i.strip()]

    style_key = call.get_variable("voice_style") or voice_styles.DEFAULT_STYLE
    traveler_id = call.get_variable("traveler_id")
    if not traveler_id:
        traveler_id = db.insert_traveler(
            name=call.get_variable("caller_name") or "Caller", phone=caller_phone(call)
        )
    db.insert_traveler_profile(traveler_id, pace=pace, interests=interests,
                               spend_priorities=spend_priorities, voice_style=style_key)
    trip_id = db.insert_trip(traveler_id, destination=destination, days=call.get_field("trip_length_days") or 3,
                              total_budget=float(total_budget))

    call.set_variable("trip_id", trip_id)
    call.set_variable("traveler_id", traveler_id)
    status_store.set_trip_id(trip_id)

    split = budget.category_budget_split(float(total_budget), spend_priorities)
    db.insert_category_budgets(trip_id, split)

    city = destination.split(",")[0].strip()
    proposed_hotels = hotels.propose_hotels(trip_id, city, interests, count=1)
    proposed_restaurants = restaurants.propose_restaurants(trip_id, city, interests, count=1)
    proposed_experiences = experiences.propose_experiences(trip_id, city, interests, count=1)

    summary_parts = []
    if proposed_hotels:
        summary_parts.append(
            "hotel: " + ", ".join(f"{h['name']} (${h['cost']:.0f})" for h in proposed_hotels)
        )
    if proposed_restaurants:
        summary_parts.append(
            "restaurant: " + ", ".join(f"{r['name']} ({r['price_tier']})" for r in proposed_restaurants)
        )
    if proposed_experiences:
        summary_parts.append(
            "experience: " + ", ".join(f"{e['name']} (${e['cost']:.0f})" for e in proposed_experiences)
        )

    call.send_instruction(
        "Share these trip ideas gradually — this is a phone call, not a list to read out. "
        "Mention just the hotel first (name and what makes it a good fit, skip the price unless "
        "asked) and pause for their reaction. Only after they respond, bring up the restaurant; "
        "only after that, the experience. Never state more than one option in a single turn. "
        "Here's what's available if it comes up: " + "; ".join(summary_parts) + ". "
        f"Their total budget is ${total_budget}, but lead with the places, not the numbers. "
        "They can add, remove, or ask about budget at any point."
    )

    call.set_task(
        "trip_planning",
        objective=(
            "Keep helping the traveler plan this trip: propose, add, or remove hotels, "
            "restaurants, and experiences, answer budget questions, and walk through budget "
            "tradeoffs if something they want doesn't fit. Keep every turn short and focused on "
            "one thing at a time — never stack multiple options, prices, or follow-up questions "
            "into a single response. After you finish handling each request, ask if there's "
            "anything else you can help them plan."
        ),
        completion_criteria=(
            "The caller has said they're happy with the plan and don't need help with anything "
            "else, or they've explicitly asked to finalize or wrap up the trip."
        ),
    )
    logger.info("Trip intake complete for trip %s (%s)", trip_id, destination)


@agent.on_task_complete("trip_planning")
def on_trip_planning_complete(call: guava.Call):
    finalize_trip(call, closing_note="Thank them warmly for planning with Nomi and say goodbye.")


def caller_phone(call: guava.Call) -> str | None:
    """Caller ID, when there is one. Chat, local, and webrtc channels have none."""
    try:
        call_info = call.call_info
        if call_info and call_info.call_type == "pstn":
            return call_info.from_number
    except Exception:  # noqa: BLE001 - never block a call over caller ID
        logger.debug("No caller ID available on this channel", exc_info=True)
    return None
