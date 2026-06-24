from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from api.sqlite_utils import connect_sqlite


class UsageStore:
    def __init__(self, path: str | Path = "runtime_data/usage.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS usage_events (
                    event_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    source TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def record(self, user_id: str, event_type: str, quantity: float, source: str, metadata: dict[str, Any] | None = None) -> dict:
        event_id = "usage_" + uuid4().hex[:12]
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO usage_events (event_id, user_id, event_type, quantity, source, metadata_json) VALUES (?, ?, ?, ?, ?, ?)",
                (event_id, user_id, event_type, quantity, source, json.dumps(metadata or {}, ensure_ascii=False)),
            )
        return self.get(event_id) or {}

    def get(self, event_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM usage_events WHERE event_id = ?", (event_id,)).fetchone()
        return dict(row) if row else None

    def list_events(self, user_id: str | None = None, limit: int = 100) -> list[dict]:
        with self.connect() as conn:
            if user_id:
                rows = conn.execute("SELECT * FROM usage_events WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM usage_events ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

    def summary(self, user_id: str = "local") -> dict:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT event_type, SUM(quantity) AS total FROM usage_events WHERE user_id = ? GROUP BY event_type",
                (user_id,),
            ).fetchall()
            total_events = conn.execute("SELECT COUNT(*) FROM usage_events WHERE user_id = ?", (user_id,)).fetchone()[0]
        by_type = {row["event_type"]: row["total"] for row in rows}
        return {"user_id": user_id, "total_events": total_events, "by_type": by_type}
