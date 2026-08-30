"""Judge-facing local dashboard. Run separately from the agent process:

    uv run uvicorn dashboard:app --port 8787

Reads claims.db and call_status.json, both written by the agent process.
Never imported by main.py — if this crashes, the phone demo is unaffected.
"""

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.storage import init_db, list_claims
from app.status_store import get_status, get_transcript

app = FastAPI()

init_db()


@app.get("/api/claims")
def api_claims():
    return list_claims()


@app.get("/api/status")
def api_status():
    return get_status()


@app.get("/api/transcript")
def api_transcript():
    return get_transcript()


app.mount("/", StaticFiles(directory="static", html=True), name="static")
