import logging

import guava

from concierge_app import db
from concierge_app.agent import agent
from concierge_app.specialists import budget

logger = logging.getLogger("concierge.questions")


@agent.on_question
def on_question(call: guava.Call, question: str) -> str:
    logger.info("Question received: %s", question)
    trip_id = call.get_variable("trip_id")
    if not trip_id:
        return "No trip has been started yet."

    trip = db.get_trip(trip_id)
    items = db.list_itinerary_items(trip_id)
    spent = budget.committed_and_proposed_total(trip_id)
    remaining = trip["total_budget"] - spent

    lines = [
        f"Budget: ${spent:.0f} allocated of ${trip['total_budget']:.0f} total, ${remaining:.0f} remaining."
    ]
    for item in items:
        day = f" on {item['day_date']}" if item["day_date"] else ""
        lines.append(f"{item['item_type']}: {item['title']} (${item['cost']:.0f}, {item['status']}){day}")

    answer = " ".join(lines)
    logger.info("Answering: %s", answer)
    return answer
