"""Judge-facing local dashboard for Concierge. Run separately from the agent:

    uv run uvicorn concierge_dashboard:app --port 8788

Reads concierge.db directly, written by the concierge_app agent process.
"""

import sqlite3

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from concierge_app import status_store
from concierge_app.db import DB_PATH, init_db

app = FastAPI()

init_db()


@app.get("/api/status")
def api_status():
    return status_store.get_status()


@app.get("/api/transcript")
def api_transcript():
    return status_store.get_transcript()


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/api/trip")
def api_trip():
    conn = _connect()
    trip = conn.execute("SELECT * FROM trips ORDER BY created_at DESC LIMIT 1").fetchone()
    conn.close()
    return dict(trip) if trip else None


@app.get("/api/itinerary")
def api_itinerary():
    conn = _connect()
    trip = conn.execute("SELECT * FROM trips ORDER BY created_at DESC LIMIT 1").fetchone()
    if not trip:
        conn.close()
        return []
    items = conn.execute(
        "SELECT * FROM itinerary_items WHERE trip_id = ? AND status != 'removed' "
        "ORDER BY day_date, start_time",
        (trip["id"],),
    ).fetchall()
    conn.close()
    return [dict(i) for i in items]


@app.get("/api/comic")
def api_comic():
    conn = _connect()
    trip = conn.execute("SELECT * FROM trips ORDER BY created_at DESC LIMIT 1").fetchone()
    if not trip:
        conn.close()
        return None
    comic = conn.execute(
        "SELECT * FROM trip_comics WHERE trip_id = ? ORDER BY created_at DESC LIMIT 1",
        (trip["id"],),
    ).fetchone()
    conn.close()
    if comic:
        return {"image_url": comic["image_url"], "fallback": False}
    if trip["status"] == "finalized":
        return {"image_url": None, "fallback": True}
    return None


app.mount("/", StaticFiles(directory="concierge_static", html=True), name="static")
