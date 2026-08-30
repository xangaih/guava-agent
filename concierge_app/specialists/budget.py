from concierge_app import db

DEFAULT_SPLIT = {"hotels": 0.30, "food": 0.25, "transport": 0.15, "experiences": 0.20, "buffer": 0.10}


def category_budget_split(total_budget: float, spend_priorities: str) -> dict[str, float]:
    split = dict(DEFAULT_SPLIT)
    text = (spend_priorities or "").lower()
    if "food" in text:
        split["food"] += 0.05
        split["hotels"] -= 0.05
    if "hotel" in text:
        split["hotels"] += 0.05
        split["food"] -= 0.05
    return {category: round(total_budget * pct, 2) for category, pct in split.items()}


def committed_and_proposed_total(trip_id: str) -> float:
    """Only confirmed items count as real spend. Proposed alternatives are
    candidates the caller hasn't committed to yet and don't consume budget."""
    items = db.list_itinerary_items(trip_id, status="confirmed")
    return sum(item["cost"] or 0 for item in items)


def check_budget(trip_id: str, additional_cost: float) -> tuple[bool, float]:
    trip = db.get_trip(trip_id)
    total_budget = trip["total_budget"] or 0
    spent = committed_and_proposed_total(trip_id)
    remaining = total_budget - spent
    return additional_cost <= remaining, remaining


def _category_table(item_type: str) -> str | None:
    return {"hotel": "hotels", "restaurant": "restaurants", "experience": "experiences"}.get(item_type)


def generate_tradeoffs(trip_id: str, item: dict, over_amount: float) -> list[dict]:
    tradeoffs = []

    table = _category_table(item.get("item_type"))
    if table:
        import sqlite3

        conn = sqlite3.connect(db.DB_PATH)
        conn.row_factory = sqlite3.Row
        if table != "restaurants":
            rows = conn.execute(
                f"SELECT * FROM {table} WHERE price < ? ORDER BY price DESC LIMIT 1",
                (item["cost"],),
            ).fetchall()
            conn.close()
            if rows:
                cheaper = dict(rows[0])
                tradeoffs.append({
                    "type": "swap",
                    "description": f"switch to {cheaper['name']} (${cheaper['price']:.0f})",
                    "saves": round(item["cost"] - cheaper["price"], 2),
                })
        else:
            conn.close()

    items = db.list_itinerary_items(trip_id, status="confirmed")
    optional_items = [i for i in items if i["priority"] == "optional"]
    if optional_items:
        drop = optional_items[-1]
        tradeoffs.append({
            "type": "remove",
            "description": f"drop {drop['title']}",
            "saves": round(drop["cost"] or 0, 2),
        })

    tradeoffs.append({
        "type": "raise_budget",
        "description": f"raise total budget by ${over_amount:.0f}",
        "saves": 0,
    })

    return tradeoffs[:3]
