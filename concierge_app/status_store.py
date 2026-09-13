from psycopg.types.json import Json

from concierge_app.db import _connect

TRANSCRIPT_LIMIT = 50
_ROW_ID = "current"


def call_started():
    conn = _connect()
    conn.execute(
        "UPDATE call_status SET active_call = true, trip_id = NULL, transcript = '[]'::jsonb, "
        "updated_at = now() WHERE id = %s",
        (_ROW_ID,),
    )
    conn.close()


def call_ended():
    conn = _connect()
    conn.execute(
        "UPDATE call_status SET active_call = false, updated_at = now() WHERE id = %s",
        (_ROW_ID,),
    )
    conn.close()


def set_trip_id(trip_id: str):
    conn = _connect()
    conn.execute(
        "UPDATE call_status SET trip_id = %s, updated_at = now() WHERE id = %s",
        (trip_id, _ROW_ID),
    )
    conn.close()


def append_transcript(speaker: str, utterance: str):
    conn = _connect()
    row = conn.execute("SELECT transcript FROM call_status WHERE id = %s", (_ROW_ID,)).fetchone()
    transcript = (row["transcript"] if row else []) or []
    transcript.append({"speaker": speaker, "utterance": utterance})
    transcript = transcript[-TRANSCRIPT_LIMIT:]
    conn.execute(
        "UPDATE call_status SET transcript = %s, updated_at = now() WHERE id = %s",
        (Json(transcript), _ROW_ID),
    )
    conn.close()


def get_status() -> dict:
    conn = _connect()
    row = conn.execute(
        "SELECT active_call, trip_id FROM call_status WHERE id = %s", (_ROW_ID,)
    ).fetchone()
    conn.close()
    if not row:
        return {"active_call": False, "trip_id": None}
    return {"active_call": row["active_call"], "trip_id": row["trip_id"]}


def get_transcript() -> list[dict]:
    conn = _connect()
    row = conn.execute(
        "SELECT transcript FROM call_status WHERE id = %s", (_ROW_ID,)
    ).fetchone()
    conn.close()
    return row["transcript"] if row else []
