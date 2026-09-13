"""Judge-facing local dashboard for Concierge. Run separately from the agent:

    uv run uvicorn concierge_dashboard:app --port 8788

Reads from the Supabase database, written by the concierge_app agent process.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from concierge_app import db, status_store
from concierge_app.db import init_db

app = FastAPI()

init_db()


@app.get("/api/status")
def api_status():
    return status_store.get_status()


@app.get("/api/transcript")
def api_transcript():
    return status_store.get_transcript()


@app.get("/api/trip")
def api_trip():
    return db.get_latest_trip()


@app.get("/api/itinerary")
def api_itinerary():
    trip = db.get_latest_trip()
    if not trip:
        return []
    return db.list_itinerary_items(trip["id"])


@app.get("/api/comic")
def api_comic():
    trip = db.get_latest_trip()
    if not trip:
        return None
    comic = db.get_latest_trip_comic(trip["id"])
    if comic:
        return {"image_url": comic["image_url"], "fallback": False}
    if trip["status"] == "finalized":
        return {"image_url": None, "fallback": True}
    return None


app.mount("/", StaticFiles(directory="concierge_static", html=True), name="static")
