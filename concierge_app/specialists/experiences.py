from concierge_app import db


def propose_experiences(trip_id: str, city: str, interests: list[str], count: int = 2) -> list[dict]:
    candidates = db.search_experiences(city, interests, limit=count)
    proposed = []
    for experience in candidates:
        item_id = db.insert_itinerary_item(
            trip_id=trip_id,
            item_type="experience",
            ref_id=experience["id"],
            title=experience["name"],
            location=experience["city"],
            cost=experience["price"],
            priority="optional",
            status="proposed",
        )
        proposed.append({"id": item_id, "item_type": "experience", "cost": experience["price"], **experience})
    return proposed
