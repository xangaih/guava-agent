import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "concierge.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS travelers (
    id TEXT PRIMARY KEY,
    name TEXT,
    phone TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS traveler_profiles (
    traveler_id TEXT PRIMARY KEY,
    pace TEXT,
    day_start TEXT,
    day_end TEXT,
    interests TEXT,
    spend_priorities TEXT,
    dietary_restrictions TEXT,
    notes TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS trips (
    id TEXT PRIMARY KEY,
    traveler_id TEXT,
    destination TEXT,
    start_date TEXT,
    end_date TEXT,
    total_budget REAL,
    status TEXT DEFAULT 'planning',
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS category_budgets (
    id TEXT PRIMARY KEY,
    trip_id TEXT,
    category TEXT,
    target_amount REAL
);

CREATE TABLE IF NOT EXISTS hotels (
    id TEXT PRIMARY KEY,
    name TEXT, neighborhood TEXT, city TEXT,
    price REAL, image_url TEXT, external_url TEXT,
    tags TEXT, lat REAL, lng REAL
);

CREATE TABLE IF NOT EXISTS restaurants (
    id TEXT PRIMARY KEY,
    name TEXT, neighborhood TEXT, city TEXT, cuisine TEXT,
    price_tier TEXT,
    image_url TEXT, external_url TEXT,
    tags TEXT, lat REAL, lng REAL
);

CREATE TABLE IF NOT EXISTS experiences (
    id TEXT PRIMARY KEY,
    name TEXT, city TEXT, category TEXT,
    price REAL, duration_minutes INTEGER,
    image_url TEXT, external_url TEXT, tags TEXT
);

CREATE TABLE IF NOT EXISTS itinerary_items (
    id TEXT PRIMARY KEY,
    trip_id TEXT,
    day_date TEXT,
    start_time TEXT, end_time TEXT,
    item_type TEXT,
    ref_id TEXT,
    title TEXT, location TEXT,
    cost REAL,
    priority TEXT DEFAULT 'anchor',
    status TEXT DEFAULT 'proposed',
    notes TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS constraint_overrides (
    id TEXT PRIMARY KEY,
    trip_id TEXT,
    constraint_name TEXT,
    profile_value TEXT,
    override_value TEXT,
    scope TEXT,
    reason TEXT,
    user_confirmed INTEGER DEFAULT 1,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS trip_comics (
    id TEXT PRIMARY KEY,
    trip_id TEXT,
    image_url TEXT,
    created_at TEXT
);
"""


def init_db():
    conn = _connect()
    conn.executescript(SCHEMA)
    conn.commit()
    if conn.execute("SELECT COUNT(*) FROM hotels").fetchone()[0] == 0:
        _seed(conn)
    conn.close()


def _seed(conn: sqlite3.Connection):
    hotels = [
        ("Nishiki Machiya Inn", "Nakagyo", "Kyoto", 145, "nishiki-machiya", ["boutique", "local", "traditional"]),
        ("Gion Ryokan Sora", "Higashiyama", "Kyoto", 290, "gion-ryokan-sora", ["boutique", "traditional", "romantic"]),
        ("Kyoto Grand Tower", "Shimogyo", "Kyoto", 310, "kyoto-grand-tower", ["large_chain", "central"]),
        ("Arashiyama Riverside Hotel", "Arashiyama", "Kyoto", 210, "arashiyama-riverside", ["central", "scenic"]),
        ("Kyoto Central Business Hotel", "Shimogyo", "Kyoto", 95, "kyoto-central-business", ["large_chain", "budget"]),
        ("Machiya Stay Kamigyo", "Kamigyo", "Kyoto", 160, "machiya-kamigyo", ["boutique", "local"]),
        ("The Kamogawa Ritz", "Kamogawa", "Kyoto", 650, "kamogawa-ritz", ["luxury", "central"]),
        ("Guesthouse Sakura", "Fushimi", "Kyoto", 60, "guesthouse-sakura", ["budget", "hostel"]),
    ]
    for name, neighborhood, city, price, seed, tags in hotels:
        conn.execute(
            "INSERT INTO hotels (id, name, neighborhood, city, price, image_url, external_url, tags) "
            "VALUES (?, ?, ?, ?, ?, ?, '#', ?)",
            (_new_id(), name, neighborhood, city, price,
             f"https://picsum.photos/seed/{seed}/600/400", json.dumps(tags)),
        )

    restaurants = [
        ("Sushi Kanesaka Annex", "Gion", "Kyoto", "omakase", "$$$$", "sushi-kanesaka", ["splurge", "special_occasion"]),
        ("Kikunoi", "Higashiyama", "Kyoto", "kaiseki", "$$$$", "kikunoi", ["splurge", "traditional"]),
        ("Ramen Kokoro", "Kawaramachi", "Kyoto", "ramen", "$", "ramen-kokoro", ["casual", "local"]),
        ("Nishiki Market Food Stalls", "Nakagyo", "Kyoto", "street food", "$", "nishiki-stalls", ["casual", "local"]),
        ("Yudofu Sagano", "Arashiyama", "Kyoto", "tofu kaiseki", "$$$", "yudofu-sagano", ["traditional", "vegetarian_friendly"]),
        ("Pontocho Grill House", "Pontocho", "Kyoto", "yakitori", "$$", "pontocho-grill", ["local", "nightlife"]),
        ("Kyoto Curry Standing", "Shimogyo", "Kyoto", "curry", "$", "kyoto-curry", ["casual", "quick"]),
        ("Gion Kappa Sushi Bar", "Gion", "Kyoto", "sushi", "$$", "gion-kappa", ["casual"]),
        ("Omen Udon", "Ginkakuji", "Kyoto", "udon", "$$", "omen-udon", ["local"]),
        ("Teppanyaki Wa", "Kamogawa", "Kyoto", "teppanyaki", "$$$", "teppanyaki-wa", ["splurge"]),
    ]
    for name, neighborhood, city, cuisine, price_tier, seed, tags in restaurants:
        conn.execute(
            "INSERT INTO restaurants (id, name, neighborhood, city, cuisine, price_tier, image_url, external_url, tags) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, '#', ?)",
            (_new_id(), name, neighborhood, city, cuisine, price_tier,
             f"https://picsum.photos/seed/{seed}/600/400", json.dumps(tags)),
        )

    experiences = [
        ("Kiyomizu-dera Architecture Walk", "Kyoto", "architecture", 45, 90, "kiyomizu-dera", ["temple", "architecture", "walkable"]),
        ("Fushimi Inari Torii Hike", "Kyoto", "nature", 0, 120, "fushimi-inari", ["nature", "adventure", "free"]),
        ("Arashiyama Bamboo Grove & Tenryu-ji", "Kyoto", "nature", 20, 90, "arashiyama-bamboo", ["nature", "architecture"]),
        ("Traditional Tea Ceremony", "Kyoto", "cultural", 60, 60, "tea-ceremony", ["cultural", "local"]),
        ("Nishiki Market Food Tour", "Kyoto", "food", 85, 120, "nishiki-food-tour", ["food", "local"]),
        ("Gion Evening District Walk", "Kyoto", "cultural", 35, 90, "gion-evening-walk", ["cultural", "nightlife"]),
        ("Kimono Rental & Photo Walk", "Kyoto", "cultural", 70, 180, "kimono-photo-walk", ["cultural", "design"]),
    ]
    for name, city, category, price, duration, seed, tags in experiences:
        conn.execute(
            "INSERT INTO experiences (id, name, city, category, price, duration_minutes, image_url, external_url, tags) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, '#', ?)",
            (_new_id(), name, city, category, price, duration,
             f"https://picsum.photos/seed/{seed}/600/400", json.dumps(tags)),
        )
    conn.commit()


def insert_traveler(name: str, phone: str | None) -> str:
    traveler_id = _new_id()
    conn = _connect()
    conn.execute(
        "INSERT INTO travelers (id, name, phone, created_at) VALUES (?, ?, ?, ?)",
        (traveler_id, name, phone, _now()),
    )
    conn.commit()
    conn.close()
    return traveler_id


def insert_traveler_profile(traveler_id: str, pace: str, interests: list[str], spend_priorities: str,
                             day_start: str = "09:00", day_end: str = "23:00"):
    conn = _connect()
    conn.execute(
        "INSERT INTO traveler_profiles (traveler_id, pace, day_start, day_end, interests, "
        "spend_priorities, dietary_restrictions, notes, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (traveler_id, pace, day_start, day_end, json.dumps(interests), spend_priorities,
         json.dumps([]), "", _now()),
    )
    conn.commit()
    conn.close()


def insert_trip(traveler_id: str, destination: str, days: int, total_budget: float) -> str:
    trip_id = _new_id()
    conn = _connect()
    conn.execute(
        "INSERT INTO trips (id, traveler_id, destination, start_date, end_date, total_budget, status, created_at) "
        "VALUES (?, ?, ?, NULL, NULL, ?, 'planning', ?)",
        (trip_id, traveler_id, destination, total_budget, _now()),
    )
    conn.commit()
    conn.close()
    return trip_id


def get_trip(trip_id: str) -> dict | None:
    conn = _connect()
    row = conn.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_traveler_profile(traveler_id: str) -> dict | None:
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM traveler_profiles WHERE traveler_id = ?", (traveler_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    data["interests"] = json.loads(data["interests"] or "[]")
    data["dietary_restrictions"] = json.loads(data["dietary_restrictions"] or "[]")
    return data


def insert_category_budgets(trip_id: str, split: dict[str, float]):
    conn = _connect()
    for category, amount in split.items():
        conn.execute(
            "INSERT INTO category_budgets (id, trip_id, category, target_amount) VALUES (?, ?, ?, ?)",
            (_new_id(), trip_id, category, amount),
        )
    conn.commit()
    conn.close()


def search_hotels(city: str, interests: list[str], limit: int = 3) -> list[dict]:
    return _search_by_tags("hotels", city, interests, limit)


def search_restaurants(city: str, interests: list[str], limit: int = 3) -> list[dict]:
    return _search_by_tags("restaurants", city, interests, limit)


def search_experiences(city: str, interests: list[str], limit: int = 3) -> list[dict]:
    return _search_by_tags("experiences", city, interests, limit)


def _search_by_tags(table: str, city: str, interests: list[str], limit: int) -> list[dict]:
    conn = _connect()
    rows = conn.execute(f"SELECT * FROM {table} WHERE city = ?", (city,)).fetchall()
    conn.close()
    items = [dict(r) for r in rows]
    for item in items:
        item["tags"] = json.loads(item["tags"] or "[]")

    def overlap(item):
        return len(set(item["tags"]) & set(t.lower() for t in interests))

    items.sort(key=overlap, reverse=True)
    return items[:limit]


def insert_itinerary_item(trip_id: str, item_type: str, ref_id: str | None, title: str,
                           location: str, cost: float, day_date: str | None = None,
                           start_time: str | None = None, end_time: str | None = None,
                           priority: str = "anchor", status: str = "proposed") -> str:
    item_id = _new_id()
    conn = _connect()
    conn.execute(
        "INSERT INTO itinerary_items (id, trip_id, day_date, start_time, end_time, item_type, "
        "ref_id, title, location, cost, priority, status, notes, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', ?)",
        (item_id, trip_id, day_date, start_time, end_time, item_type, ref_id, title,
         location, cost, priority, status, _now()),
    )
    conn.commit()
    conn.close()
    return item_id


def update_itinerary_item(item_id: str, **fields):
    if not fields:
        return
    conn = _connect()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(f"UPDATE itinerary_items SET {set_clause} WHERE id = ?", (*fields.values(), item_id))
    conn.commit()
    conn.close()


def list_itinerary_items(trip_id: str, status: str | None = None) -> list[dict]:
    conn = _connect()
    if status:
        rows = conn.execute(
            "SELECT * FROM itinerary_items WHERE trip_id = ? AND status = ? ORDER BY day_date, start_time",
            (trip_id, status),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM itinerary_items WHERE trip_id = ? AND status != 'removed' ORDER BY day_date, start_time",
            (trip_id,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_constraint_override(trip_id: str, constraint_name: str, profile_value: str,
                                override_value: str, scope: str, reason: str):
    conn = _connect()
    conn.execute(
        "INSERT INTO constraint_overrides (id, trip_id, constraint_name, profile_value, "
        "override_value, scope, reason, user_confirmed, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)",
        (_new_id(), trip_id, constraint_name, profile_value, override_value, scope, reason, _now()),
    )
    conn.commit()
    conn.close()


def insert_trip_comic(trip_id: str, image_url: str):
    conn = _connect()
    conn.execute(
        "INSERT INTO trip_comics (id, trip_id, image_url, created_at) VALUES (?, ?, ?, ?)",
        (_new_id(), trip_id, image_url, _now()),
    )
    conn.commit()
    conn.close()


def get_latest_trip_comic(trip_id: str) -> dict | None:
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM trip_comics WHERE trip_id = ? ORDER BY created_at DESC LIMIT 1", (trip_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None
