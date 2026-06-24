from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import uuid4

from api.sqlite_utils import connect_sqlite


class GuardianRegistry:
    """Stores guardian metadata only. It never stores secret material."""

    def __init__(self, path: str | Path = "runtime_data/secure_runtime.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS guardians (
                    guardian_id TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    role TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def add_guardian(self, label: str, role: str = "runtime-approval") -> dict:
        guardian_id = "guard_" + uuid4().hex[:12]
        with self.connect() as conn:
            conn.execute("INSERT INTO guardians (guardian_id, label, role, active) VALUES (?, ?, ?, 1)", (guardian_id, label, role))
        return self.get(guardian_id) or {}

    def get(self, guardian_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM guardians WHERE guardian_id = ?", (guardian_id,)).fetchone()
        return self._row(dict(row)) if row else None

    def list_active(self) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM guardians WHERE active = 1 ORDER BY created_at ASC").fetchall()
        return [self._row(dict(row)) for row in rows]

    @staticmethod
    def _row(item: dict) -> dict:
        item["active"] = bool(item["active"])
        return item
