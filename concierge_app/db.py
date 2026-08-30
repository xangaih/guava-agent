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
        ("Le Marais Boutique Hotel", "Le Marais", "Paris", 210, "paris-marais", ["boutique", "central", "romantic"]),
        ("Saint-Germain Garden Suites", "Saint-Germain-des-Prés", "Paris", 340, "paris-germain", ["boutique", "romantic", "central"]),
        ("Montmartre Artist's Loft", "Montmartre", "Paris", 150, "paris-montmartre", ["boutique", "local", "scenic"]),
        ("Champs-Élysées Grand Hotel", "Champs-Élysées", "Paris", 480, "paris-champs", ["luxury", "central", "large_chain"]),
        ("Latin Quarter Budget Inn", "Latin Quarter", "Paris", 85, "paris-latin", ["budget", "central"]),
        ("Canal Saint-Martin Hostel", "Canal Saint-Martin", "Paris", 55, "paris-canal", ["budget", "hostel", "local"]),
        ("Trastevere Terrace Inn", "Trastevere", "Rome", 175, "rome-trastevere", ["boutique", "local", "scenic"]),
        ("Centro Storico Palazzo", "Centro Storico", "Rome", 320, "rome-centro", ["boutique", "luxury", "central"]),
        ("Monti Design Hotel", "Monti", "Rome", 195, "rome-monti", ["boutique", "design", "central"]),
        ("Prati Business Suites", "Prati", "Rome", 140, "rome-prati", ["business", "central"]),
        ("Testaccio Budget Rooms", "Testaccio", "Rome", 70, "rome-testaccio", ["budget", "local"]),
        ("Trevi Fountain Hostel", "Trevi", "Rome", 50, "rome-trevi", ["budget", "hostel", "central"]),
        ("Gràcia Garden Hotel", "Gràcia", "Barcelona", 165, "bcn-gracia", ["boutique", "local", "scenic"]),
        ("El Born Boutique Suites", "El Born", "Barcelona", 230, "bcn-born", ["boutique", "romantic", "central"]),
        ("Eixample Modernist Hotel", "Eixample", "Barcelona", 280, "bcn-eixample", ["boutique", "design", "central"]),
        ("Barceloneta Beach Resort", "Barceloneta", "Barcelona", 310, "bcn-barceloneta", ["luxury", "scenic", "large_chain"]),
        ("Raval Budget Inn", "Raval", "Barcelona", 75, "bcn-raval", ["budget", "local"]),
        ("Gothic Quarter Hostel", "Gothic Quarter", "Barcelona", 45, "bcn-gothic", ["budget", "hostel", "central"]),
        ("Shibuya Sky Suites", "Shibuya", "Tokyo", 260, "tokyo-shibuya", ["central", "large_chain"]),
        ("Shinjuku Boutique Ryokan", "Shinjuku", "Tokyo", 190, "tokyo-shinjuku", ["boutique", "traditional", "central"]),
        ("Asakusa Machiya Inn", "Asakusa", "Tokyo", 130, "tokyo-asakusa", ["boutique", "local", "traditional"]),
        ("Ginza Grand Hotel", "Ginza", "Tokyo", 420, "tokyo-ginza", ["luxury", "central"]),
        ("Nakameguro Design Hotel", "Nakameguro", "Tokyo", 175, "tokyo-nakameguro", ["boutique", "design", "scenic"]),
        ("Kichijoji Guesthouse", "Kichijoji", "Tokyo", 60, "tokyo-kichijoji", ["budget", "hostel", "local"]),
        ("Sukhumvit Sky Hotel", "Sukhumvit", "Bangkok", 120, "bkk-sukhumvit", ["central", "large_chain"]),
        ("Old Town Heritage Inn", "Old Town", "Bangkok", 90, "bkk-oldtown", ["boutique", "traditional", "local"]),
        ("Thonglor Design Loft", "Thonglor", "Bangkok", 140, "bkk-thonglor", ["boutique", "design"]),
        ("Riverside Grand Resort", "Riverside", "Bangkok", 260, "bkk-riverside", ["luxury", "scenic"]),
        ("Chinatown Budget Rooms", "Chinatown", "Bangkok", 45, "bkk-chinatown", ["budget", "local"]),
        ("Silom Backpacker Hostel", "Silom", "Bangkok", 25, "bkk-silom", ["budget", "hostel"]),
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
        ("Le Petit Bistrot", "Le Marais", "Paris", "French bistro", "$$$", "paris-bistrot", ["traditional", "romantic"]),
        ("L'Atelier Doré", "Saint-Germain-des-Prés", "Paris", "fine dining", "$$$$", "paris-atelier", ["splurge", "special_occasion"]),
        ("Marché des Enfants Rouges", "Le Marais", "Paris", "street food", "$", "paris-marche", ["casual", "local"]),
        ("Chez Léon Creperie", "Montmartre", "Paris", "crepes", "$", "paris-creperie", ["casual", "quick"]),
        ("Le Comptoir du Vin", "Saint-Germain-des-Prés", "Paris", "wine bar", "$$", "paris-comptoir", ["local", "nightlife"]),
        ("Falafel Ben's", "Le Marais", "Paris", "falafel", "$", "paris-falafel", ["casual", "vegetarian_friendly"]),
        ("Brasserie de la Seine", "Champs-Élysées", "Paris", "brasserie", "$$$", "paris-brasserie", ["traditional", "central"]),
        ("La Table Verte", "Latin Quarter", "Paris", "vegetarian", "$$", "paris-verte", ["vegetarian_friendly", "casual"]),
        ("Trattoria della Nonna", "Trastevere", "Rome", "traditional Roman", "$$$", "rome-nonna", ["traditional", "local"]),
        ("Osteria del Pantheon", "Centro Storico", "Rome", "Italian fine dining", "$$$$", "rome-osteria", ["splurge", "special_occasion"]),
        ("Pizza al Taglio Monti", "Monti", "Rome", "pizza", "$", "rome-pizza", ["casual", "quick"]),
        ("Mercato Testaccio Stalls", "Testaccio", "Rome", "street food", "$", "rome-mercato", ["casual", "local"]),
        ("Cacio e Pepe House", "Trastevere", "Rome", "pasta", "$$", "rome-cacio", ["traditional", "local"]),
        ("Gelateria Antica", "Centro Storico", "Rome", "gelato", "$", "rome-gelateria", ["casual", "quick"]),
        ("Vino e Cucina", "Monti", "Rome", "wine bar", "$$", "rome-vino", ["local", "nightlife"]),
        ("Verde Roma", "Prati", "Rome", "vegetarian", "$$", "rome-verde", ["vegetarian_friendly", "casual"]),
        ("Can Culleretes", "Gothic Quarter", "Barcelona", "Catalan", "$$$", "bcn-culleretes", ["traditional", "local"]),
        ("Tickets Tapas Bar", "El Born", "Barcelona", "tapas fine dining", "$$$$", "bcn-tickets", ["splurge", "special_occasion"]),
        ("Mercat de la Boqueria Stalls", "Raval", "Barcelona", "street food", "$", "bcn-boqueria", ["casual", "local"]),
        ("Bar del Pla", "El Born", "Barcelona", "tapas", "$$", "bcn-bardelpla", ["local", "nightlife"]),
        ("La Paradeta Seafood", "Barceloneta", "Barcelona", "seafood", "$$", "bcn-paradeta", ["casual", "local"]),
        ("Flax & Kale", "Raval", "Barcelona", "vegetarian", "$$", "bcn-flaxkale", ["vegetarian_friendly", "casual"]),
        ("Xurreria Central", "Gothic Quarter", "Barcelona", "churros", "$", "bcn-xurreria", ["casual", "quick"]),
        ("Disfrutar", "Eixample", "Barcelona", "avant-garde tasting menu", "$$$$", "bcn-disfrutar", ["splurge", "special_occasion"]),
        ("Sushi Saito Annex", "Ginza", "Tokyo", "omakase", "$$$$", "tokyo-saito", ["splurge", "special_occasion"]),
        ("Ichiran Ramen", "Shibuya", "Tokyo", "ramen", "$", "tokyo-ichiran", ["casual", "quick"]),
        ("Asakusa Tempura House", "Asakusa", "Tokyo", "tempura", "$$$", "tokyo-tempura", ["traditional", "local"]),
        ("Nakameguro Izakaya", "Nakameguro", "Tokyo", "izakaya", "$$", "tokyo-izakaya", ["local", "nightlife"]),
        ("Tsukiji Outer Market Stalls", "Ginza", "Tokyo", "street food", "$", "tokyo-tsukiji", ["casual", "local"]),
        ("Shinjuku Yakitori Alley", "Shinjuku", "Tokyo", "yakitori", "$$", "tokyo-yakitori", ["local", "nightlife"]),
        ("Kichijoji Curry Kitchen", "Kichijoji", "Tokyo", "curry", "$", "tokyo-curry", ["casual", "quick"]),
        ("Vegan Ramen Uzu", "Shibuya", "Tokyo", "vegan ramen", "$$", "tokyo-uzu", ["vegetarian_friendly", "casual"]),
        ("Sorn Southern Thai", "Thonglor", "Bangkok", "southern thai fine dining", "$$$$", "bkk-sorn", ["splurge", "special_occasion"]),
        ("Jay Fai Street Kitchen", "Old Town", "Bangkok", "street food", "$$", "bkk-jayfai", ["casual", "local"]),
        ("Chinatown Noodle Stalls", "Chinatown", "Bangkok", "noodles", "$", "bkk-noodles", ["casual", "quick"]),
        ("Riverside Thai Terrace", "Riverside", "Bangkok", "thai fine dining", "$$$", "bkk-terrace", ["traditional", "scenic"]),
        ("Sukhumvit Som Tam House", "Sukhumvit", "Bangkok", "som tam", "$", "bkk-somtam", ["casual", "local"]),
        ("Thonglor Rooftop Bar & Grill", "Thonglor", "Bangkok", "grill", "$$$", "bkk-rooftop", ["nightlife", "local"]),
        ("Silom Vegetarian Kitchen", "Silom", "Bangkok", "vegetarian thai", "$$", "bkk-silomveg", ["vegetarian_friendly", "casual"]),
        ("Chatuchak Weekend Bites", "Chinatown", "Bangkok", "street food", "$", "bkk-chatuchak", ["casual", "local"]),
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
        ("Louvre Architecture Walk", "Paris", "architecture", 25, 120, "paris-louvre", ["architecture", "walkable"]),
        ("Seine River Sunset Cruise", "Paris", "scenic", 40, 60, "paris-seine", ["scenic", "romantic"]),
        ("Montmartre Street Art Tour", "Paris", "cultural", 30, 90, "paris-streetart", ["cultural", "local"]),
        ("Père Lachaise History Walk", "Paris", "architecture", 0, 90, "paris-lachaise", ["free", "architecture", "walkable"]),
        ("Wine & Cheese Tasting", "Paris", "food", 65, 90, "paris-winecheese", ["food", "local"]),
        ("Palais Garnier Opera Tour", "Paris", "cultural", 20, 60, "paris-garnier", ["cultural", "architecture"]),
        ("Colosseum Architecture Tour", "Rome", "architecture", 55, 120, "rome-colosseum", ["architecture", "walkable"]),
        ("Vatican Museums & Sistine Chapel", "Rome", "cultural", 45, 150, "rome-vatican", ["cultural", "architecture"]),
        ("Trastevere Evening Walk", "Rome", "cultural", 0, 90, "rome-trastevere-walk", ["free", "cultural", "local"]),
        ("Roman Cooking Class", "Rome", "food", 90, 150, "rome-cooking", ["food", "local"]),
        ("Appian Way Bike Tour", "Rome", "adventure", 35, 120, "rome-appian", ["adventure", "nature"]),
        ("Borghese Gallery Art Walk", "Rome", "architecture", 30, 90, "rome-borghese", ["architecture", "cultural"]),
        ("Sagrada Familia Architecture Tour", "Barcelona", "architecture", 35, 90, "bcn-sagrada", ["architecture", "walkable"]),
        ("Park Güell Design Walk", "Barcelona", "architecture", 20, 90, "bcn-guell", ["architecture", "design"]),
        ("Gothic Quarter Free Walking Tour", "Barcelona", "cultural", 0, 120, "bcn-gothicwalk", ["free", "cultural", "walkable"]),
        ("Flamenco Night Show", "Barcelona", "cultural", 45, 60, "bcn-flamenco", ["cultural", "nightlife"]),
        ("Barceloneta Beach Kayaking", "Barcelona", "adventure", 40, 90, "bcn-kayak", ["adventure", "nature"]),
        ("Catalan Cooking Class", "Barcelona", "food", 80, 150, "bcn-cooking", ["food", "local"]),
        ("Senso-ji Temple Architecture Walk", "Tokyo", "architecture", 0, 90, "tokyo-sensoji", ["free", "architecture", "walkable"]),
        ("teamLab Digital Art Museum", "Tokyo", "cultural", 35, 120, "tokyo-teamlab", ["cultural", "design"]),
        ("Shibuya Crossing Night Walk", "Tokyo", "cultural", 0, 60, "tokyo-shibuyanight", ["free", "cultural", "nightlife"]),
        ("Tokyo Sushi Making Class", "Tokyo", "food", 75, 120, "tokyo-sushiclass", ["food", "local"]),
        ("Mt. Takao Nature Hike", "Tokyo", "nature", 15, 180, "tokyo-takao", ["nature", "adventure"]),
        ("Meiji Shrine & Harajuku Walk", "Tokyo", "architecture", 0, 90, "tokyo-meiji", ["free", "architecture", "cultural"]),
        ("Grand Palace Architecture Tour", "Bangkok", "architecture", 25, 120, "bkk-grandpalace", ["architecture", "walkable"]),
        ("Chao Phraya River Cruise", "Bangkok", "scenic", 30, 90, "bkk-chaophraya", ["scenic", "romantic"]),
        ("Chatuchak Weekend Market Walk", "Bangkok", "cultural", 0, 120, "bkk-chatuchakwalk", ["free", "cultural", "local"]),
        ("Thai Cooking Class", "Bangkok", "food", 60, 150, "bkk-cooking", ["food", "local"]),
        ("Muay Thai Show Night", "Bangkok", "cultural", 40, 90, "bkk-muaythai", ["cultural", "nightlife"]),
        ("Floating Market Boat Tour", "Bangkok", "adventure", 45, 180, "bkk-floatingmarket", ["adventure", "nature"]),
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
    rows = conn.execute(f"SELECT * FROM {table} WHERE city = ? COLLATE NOCASE", (city,)).fetchall()
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
