from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from api.sqlite_utils import connect_sqlite


class ModelCommitRegistry:
    def __init__(self, path: str | Path = "runtime_data/decentralized_ledger.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS model_commits (
                    commit_id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    model_hash TEXT NOT NULL,
                    source_proof_hash TEXT NOT NULL,
                    quality_score REAL NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def register(self, model_name: str, model_version: str, model_hash: str, source_proof_hash: str, quality_score: float, metadata: dict[str, Any] | None = None) -> dict:
        commit_id = "mcommit_" + uuid4().hex[:12]
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO model_commits (commit_id, model_name, model_version, model_hash, source_proof_hash, quality_score, metadata_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (commit_id, model_name, model_version, model_hash, source_proof_hash, quality_score, json.dumps(metadata or {}, ensure_ascii=False)),
            )
        return self.get(commit_id) or {}

    def get(self, commit_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM model_commits WHERE commit_id = ?", (commit_id,)).fetchone()
        return self._row(dict(row)) if row else None

    def list_commits(self, limit: int = 100) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM model_commits ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._row(dict(row)) for row in rows]

    @staticmethod
    def _row(item: dict) -> dict:
        item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
        return item
