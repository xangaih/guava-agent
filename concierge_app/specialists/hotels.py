from concierge_app import db


def propose_hotels(trip_id: str, city: str, interests: list[str], count: int = 2) -> list[dict]:
    candidates = db.search_hotels(city, interests, limit=count)
    proposed = []
    for hotel in candidates:
        item_id = db.insert_itinerary_item(
            trip_id=trip_id,
            item_type="hotel",
            ref_id=hotel["id"],
            title=hotel["name"],
            location=f"{hotel['neighborhood']}, {hotel['city']}",
            cost=hotel["price"],
            priority="anchor",
            status="proposed",
        )
        proposed.append({"id": item_id, "item_type": "hotel", "cost": hotel["price"], **hotel})
    return proposed
