from concierge_app import db

PRICE_TIER_ESTIMATE = {"$": 15, "$$": 40, "$$$": 80, "$$$$": 150}


def propose_restaurants(trip_id: str, city: str, interests: list[str], count: int = 2) -> list[dict]:
    candidates = db.search_restaurants(city, interests, limit=count)
    proposed = []
    for restaurant in candidates:
        cost = PRICE_TIER_ESTIMATE.get(restaurant["price_tier"], 40)
        item_id = db.insert_itinerary_item(
            trip_id=trip_id,
            item_type="restaurant",
            ref_id=restaurant["id"],
            title=restaurant["name"],
            location=f"{restaurant['neighborhood']}, {restaurant['city']}",
            cost=cost,
            priority="optional",
            status="proposed",
        )
        proposed.append({"id": item_id, "item_type": "restaurant", "cost": cost, **restaurant})
    return proposed
