import json
from pathlib import Path
from typing import Any

STATUS_PATH = Path(__file__).resolve().parent.parent / "call_status.json"
TRANSCRIPT_LIMIT = 50

_DEFAULT: dict[str, Any] = {"active_call": False, "customer": None, "transcript": []}


def _read() -> dict[str, Any]:
    if not STATUS_PATH.exists():
        return dict(_DEFAULT)
    try:
        return json.loads(STATUS_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT)


def _write(data: dict[str, Any]):
    STATUS_PATH.write_text(json.dumps(data))


def call_started(customer: dict | None):
    _write({"active_call": True, "customer": customer, "transcript": []})


def call_ended():
    data = _read()
    data["active_call"] = False
    _write(data)


def append_transcript(speaker: str, utterance: str):
    data = _read()
    transcript = data.setdefault("transcript", [])
    transcript.append({"speaker": speaker, "utterance": utterance})
    data["transcript"] = transcript[-TRANSCRIPT_LIMIT:]
    _write(data)


def get_status() -> dict:
    data = _read()
    return {"active_call": data.get("active_call", False), "customer": data.get("customer")}


def get_transcript() -> list[dict]:
    return _read().get("transcript", [])
