from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from api.sqlite_utils import connect_sqlite


ALLOWED_DATA_SOURCE_TYPES = {
    "owner_authorized",
    "partner",
    "licensed",
    "uploaded",
    "public_domain",
    "open_dataset",
}

ALLOWED_USES = {"index", "rag", "inference", "finetune", "pretrain", "eval"}
ACTIVE_STATUSES = {"active"}


class DataRightsStore:
    """Stores permission records for Ailovanta training data sources."""

    def __init__(self, path: str | Path = "runtime_data/data_rights.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS data_sources (
                    source_id TEXT PRIMARY KEY,
                    source_uri TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    authorized_by TEXT NOT NULL,
                    authorization_basis TEXT NOT NULL,
                    allowed_uses_json TEXT NOT NULL,
                    scope_note TEXT NOT NULL DEFAULT '',
                    proof_uri TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def register(self, body: dict[str, Any]) -> dict:
        source_type = str(body.get("source_type", "")).strip()
        if source_type not in ALLOWED_DATA_SOURCE_TYPES:
            raise ValueError(f"unsupported data source type: {source_type}")

        allowed_uses = body.get("allowed_uses") or []
        if not isinstance(allowed_uses, list) or not allowed_uses:
            raise ValueError("allowed_uses must be a non-empty list")
        unknown_uses = sorted(set(str(item) for item in allowed_uses) - ALLOWED_USES)
        if unknown_uses:
            raise ValueError(f"unsupported allowed uses: {unknown_uses}")

        source_id = body.get("source_id") or "src_" + uuid4().hex[:12]
        status = str(body.get("status") or "active")
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO data_sources (
                    source_id, source_uri, source_type, authorized_by, authorization_basis,
                    allowed_uses_json, scope_note, proof_uri, status, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    source_id,
                    str(body["source_uri"]),
                    source_type,
                    str(body["authorized_by"]),
                    str(body["authorization_basis"]),
                    json.dumps(sorted(set(str(item) for item in allowed_uses)), ensure_ascii=False),
                    str(body.get("scope_note", "")),
                    str(body.get("proof_uri", "")),
                    status,
                ),
            )
        return self.get(source_id) or {}

    def get(self, source_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM data_sources WHERE source_id = ?", (source_id,)).fetchone()
        if not row:
            return None
        return self._api_source(dict(row))

    def list_sources(self, status: str | None = None, limit: int = 100) -> list[dict]:
        with self.connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM data_sources WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM data_sources ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._api_source(dict(row)) for row in rows]

    def check_use(self, source_id: str, requested_use: str) -> dict:
        source = self.get(source_id)
        if not source:
            return {"authorized": False, "reason": "source not found"}
        if source["status"] not in ACTIVE_STATUSES:
            return {"authorized": False, "source": source, "reason": "source is not active"}
        if requested_use not in source["allowed_uses"]:
            return {"authorized": False, "source": source, "reason": f"use not allowed: {requested_use}"}
        return {"authorized": True, "source": source, "reason": "authorized data source"}

    @staticmethod
    def _api_source(row: dict) -> dict:
        row["allowed_uses"] = json.loads(row.pop("allowed_uses_json") or "[]")
        return row
