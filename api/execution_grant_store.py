from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from api.content_addressing import hash_object


class ExecutionGrantStore:
    def __init__(self, path: str | Path = "runtime_data/secure_runtime.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS execution_grants (
                    grant_id TEXT PRIMARY KEY,
                    node_id TEXT NOT NULL,
                    package_hash TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    window_hash TEXT NOT NULL,
                    runtime_hash TEXT NOT NULL,
                    decision_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def record(self, node_id: str, package_hash: str, task_id: str, window_hash: str, runtime_hash: str, status: str, details: dict[str, Any]) -> dict:
        grant_id = "grant_" + uuid4().hex[:12]
        decision_hash = hash_object({"node_id": node_id, "package_hash": package_hash, "task_id": task_id, "window_hash": window_hash, "runtime_hash": runtime_hash, "status": status, "details": details})
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO execution_grants (grant_id, node_id, package_hash, task_id, window_hash, runtime_hash, decision_hash, status, details_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (grant_id, node_id, package_hash, task_id, window_hash, runtime_hash, decision_hash, status, json.dumps(details, ensure_ascii=False)),
            )
        return self.get(grant_id) or {}

    def get(self, grant_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM execution_grants WHERE grant_id = ?", (grant_id,)).fetchone()
        return self._row(dict(row)) if row else None

    def list_grants(self, limit: int = 100) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM execution_grants ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._row(dict(row)) for row in rows]

    @staticmethod
    def _row(item: dict) -> dict:
        item["details"] = json.loads(item.pop("details_json") or "{}")
        return item
