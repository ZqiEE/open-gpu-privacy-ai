from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4


class SourceRegistry:
    def __init__(self, path: str | Path = "runtime_data/corpus.sqlite3") -> None:
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
                CREATE TABLE IF NOT EXISTS sources (
                    source_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    base_url TEXT NOT NULL,
                    permission_scope TEXT NOT NULL,
                    allowed_for_search INTEGER NOT NULL,
                    allowed_for_training INTEGER NOT NULL,
                    allowed_for_finetune INTEGER NOT NULL,
                    allowed_for_eval INTEGER NOT NULL,
                    crawl_frequency TEXT NOT NULL DEFAULT 'manual',
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def add_source(self, body: dict[str, Any]) -> dict:
        source_id = body.get("source_id") or "src_" + uuid4().hex[:12]
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sources (
                    source_id, name, source_type, base_url, permission_scope,
                    allowed_for_search, allowed_for_training, allowed_for_finetune, allowed_for_eval,
                    crawl_frequency, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    body["name"],
                    body.get("source_type", "website"),
                    body["base_url"],
                    body.get("permission_scope", "authorized"),
                    1 if body.get("allowed_for_search", True) else 0,
                    1 if body.get("allowed_for_training", False) else 0,
                    1 if body.get("allowed_for_finetune", False) else 0,
                    1 if body.get("allowed_for_eval", True) else 0,
                    body.get("crawl_frequency", "manual"),
                    body.get("notes", ""),
                ),
            )
        return self.get_source(source_id) or {}

    def get_source(self, source_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM sources WHERE source_id = ?", (source_id,)).fetchone()
        if not row:
            return None
        return self._row(dict(row))

    def list_sources(self, limit: int = 100) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM sources ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._row(dict(row)) for row in rows]

    @staticmethod
    def _row(item: dict) -> dict:
        for key in ["allowed_for_search", "allowed_for_training", "allowed_for_finetune", "allowed_for_eval"]:
            item[key] = bool(item[key])
        return item
