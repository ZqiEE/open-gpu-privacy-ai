from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from api.migrations import MigrationRunner
from api.sqlite_utils import connect_sqlite


class ReputationOps:
    def __init__(self, path: str | Path = "runtime_data/scheduler.sqlite3") -> None:
        self.path = Path(path)
        MigrationRunner(path).run()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def add_event(self, node_id: str, event_type: str, delta: float, reason: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        event_id = "rep_" + uuid4().hex[:12]
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO node_reputation_events (event_id, node_id, event_type, delta, reason, metadata_json) VALUES (?, ?, ?, ?, ?, ?)",
                (event_id, node_id, event_type, delta, reason, json.dumps(metadata or {}, ensure_ascii=False)),
            )
            conn.execute("UPDATE nodes SET trust = MAX(0, MIN(100, trust + ?)) WHERE node_id = ?", (delta, node_id))
        return self.get_event(event_id) or {}

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM node_reputation_events WHERE event_id = ?", (event_id,)).fetchone()
        return self._api(dict(row)) if row else None

    def list_events(self, node_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            if node_id:
                rows = conn.execute("SELECT * FROM node_reputation_events WHERE node_id = ? ORDER BY created_at DESC LIMIT ?", (node_id, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM node_reputation_events ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._api(dict(row)) for row in rows]

    def scorecard(self, node_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            node = conn.execute("SELECT * FROM nodes WHERE node_id = ?", (node_id,)).fetchone()
            events = conn.execute("SELECT event_type, COUNT(*) AS count, SUM(delta) AS delta FROM node_reputation_events WHERE node_id = ? GROUP BY event_type", (node_id,)).fetchall()
            passed = conn.execute("SELECT COUNT(*) FROM verifications WHERE node_id = ? AND passed = 1", (node_id,)).fetchone()[0]
            failed = conn.execute("SELECT COUNT(*) FROM verifications WHERE node_id = ? AND passed = 0", (node_id,)).fetchone()[0]
        return {"node": dict(node) if node else None, "events": [dict(row) for row in events], "verifications": {"passed": passed, "failed": failed}}

    @staticmethod
    def _api(row: dict[str, Any]) -> dict[str, Any]:
        row["metadata"] = json.loads(row.pop("metadata_json") or "{}")
        return row
