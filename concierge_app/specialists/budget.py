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


def _neighborhood(item: dict) -> str:
    """First comma segment of an item's location — a neighborhood for hotels/restaurants,
    the city itself for experiences. Used only as a rough proximity signal, not real geodata."""
    return (item.get("location") or "").split(",")[0].strip()


def _city(item: dict) -> str:
    """Last comma segment of an item's location — always the city, for both the
    'Neighborhood, City' shape (hotels/restaurants) and the bare-city shape (experiences)."""
    return (item.get("location") or "").split(",")[-1].strip()


def generate_tradeoffs(trip_id: str, item: dict, over_amount: float) -> list[dict]:
    tradeoffs = []
    confirmed = db.list_itinerary_items(trip_id, status="confirmed")

    table = _category_table(item.get("item_type"))
    if table and table != "restaurants":
        import sqlite3

        conn = sqlite3.connect(db.DB_PATH)
        conn.row_factory = sqlite3.Row
        candidates = [dict(r) for r in conn.execute(
            f"SELECT * FROM {table} WHERE price < ? AND city = ? COLLATE NOCASE ORDER BY price DESC",
            (item["cost"], _city(item)),
        ).fetchall()]
        conn.close()
        if candidates:
            item_neighborhood = _neighborhood(item)
            same_area = next((c for c in candidates if c["neighborhood"] == item_neighborhood), None)
            cheaper = same_area or candidates[0]
            if cheaper["neighborhood"] == item_neighborhood:
                flow_note = f"stays right in {cheaper['neighborhood']}, so it won't add travel between stops"
            else:
                flow_note = (
                    f"is over in {cheaper['neighborhood']} instead of {item_neighborhood}, "
                    "a bit further from the rest of the plan"
                )
            tradeoffs.append({
                "type": "swap",
                "description": f"switch to {cheaper['name']} (${cheaper['price']:.0f}) — {flow_note}",
                "saves": round(item["cost"] - cheaper["price"], 2),
            })

    optional_items = [i for i in confirmed if i["priority"] == "optional"]
    if optional_items:
        neighborhood_counts: dict[str, int] = {}
        for i in confirmed:
            n = _neighborhood(i)
            neighborhood_counts[n] = neighborhood_counts.get(n, 0) + 1

        # Prefer dropping whichever optional item shares its neighborhood with the fewest
        # other confirmed stops — i.e. the one least woven into the rest of the day's flow.
        drop = min(optional_items, key=lambda i: neighborhood_counts.get(_neighborhood(i), 0))
        if neighborhood_counts.get(_neighborhood(drop), 0) <= 1:
            flow_note = "it's already off on its own, away from everything else you've planned"
        else:
            flow_note = "it overlaps with another stop, so the day still flows fine without it"
        tradeoffs.append({
            "type": "remove",
            "description": f"drop {drop['title']} — {flow_note}",
            "saves": round(drop["cost"] or 0, 2),
        })

    tradeoffs.append({
        "type": "raise_budget",
        "description": f"raise total budget by ${over_amount:.0f}",
        "saves": 0,
    })

    return tradeoffs[:3]
