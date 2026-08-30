import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "claims.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS claims (
            id TEXT PRIMARY KEY,
            policy_number TEXT,
            incident_date TEXT,
            description TEXT,
            callback_number TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def _mask_policy_number(policy_number: str | None) -> str | None:
    if not policy_number:
        return policy_number
    tail = policy_number[-3:]
    return "•" * max(len(policy_number) - 3, 0) + tail


def save_claim(call_id: str, fields: dict) -> str:
    confirmation_code = secrets.token_hex(3).upper()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO claims (id, policy_number, incident_date, description, callback_number, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            confirmation_code,
            _mask_policy_number(fields.get("policy_number")),
            fields.get("incident_date"),
            fields.get("description"),
            fields.get("callback_number"),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return confirmation_code


def list_claims() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM claims ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]
