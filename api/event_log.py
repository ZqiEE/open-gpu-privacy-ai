from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from api.migrations import MigrationRunner
from api.sqlite_utils import connect_sqlite


class EventLog:
    def __init__(self, path: str | Path = "runtime_data/scheduler.sqlite3") -> None:
        self.path = Path(path)
        MigrationRunner(path).run()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def write(self, level: str, source: str, message: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        event_id = "evt_" + uuid4().hex[:12]
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO app_events (event_id, level, source, message, metadata_json) VALUES (?, ?, ?, ?, ?)",
                (event_id, level, source, message, json.dumps(metadata or {}, ensure_ascii=False)),
            )
        return self.get(event_id) or {}

    def get(self, event_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM app_events WHERE event_id = ?", (event_id,)).fetchone()
        return self._api(dict(row)) if row else None

    def list(self, level: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            if level:
                rows = conn.execute("SELECT * FROM app_events WHERE level = ? ORDER BY created_at DESC LIMIT ?", (level, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM app_events ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._api(dict(row)) for row in rows]

    def summary(self) -> dict[str, Any]:
        with self.connect() as conn:
            rows = conn.execute("SELECT level, COUNT(*) AS count FROM app_events GROUP BY level").fetchall()
        return {"levels": {row["level"]: row["count"] for row in rows}}

    @staticmethod
    def _api(row: dict[str, Any]) -> dict[str, Any]:
        row["metadata"] = json.loads(row.pop("metadata_json") or "{}")
        return row
