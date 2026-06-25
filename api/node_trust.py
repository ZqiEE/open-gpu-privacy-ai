from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
from pathlib import Path
from time import time
from typing import Any

from api.sqlite_utils import connect_sqlite


def hash_secret(secret: str) -> str:
    return "sha256:" + hashlib.sha256(secret.encode("utf-8")).hexdigest()


def default_path() -> str:
    return os.getenv("AILOVANTA_NODE_TRUST_PATH", "runtime_data/node_trust.sqlite3")


class NodeTrustStore:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or default_path())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS node_trust (
                    node_id TEXT PRIMARY KEY,
                    secret_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    trust_score REAL NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_node_trust_status ON node_trust(status);
                """
            )

    def register(self, node_id: str, secret: str, status: str = "active", trust_score: float = 0.8, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        now = round(time(), 3)
        with self.connect() as conn:
            before = conn.execute("SELECT created_at FROM node_trust WHERE node_id = ?", (node_id,)).fetchone()
            conn.execute(
                """
                INSERT OR REPLACE INTO node_trust VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (node_id, hash_secret(secret), status, trust_score, __import__("json").dumps(metadata or {}, ensure_ascii=False, sort_keys=True), before[0] if before else now, now),
            )
        return self.get(node_id) or {}

    def get(self, node_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM node_trust WHERE node_id = ?", (node_id,)).fetchone()
        if not row:
            return None
        item = dict(row)
        item["metadata"] = __import__("json").loads(item.pop("metadata_json") or "{}")
        return item

    def list_nodes(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM node_trust ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            item["metadata"] = __import__("json").loads(item.pop("metadata_json") or "{}")
            items.append(item)
        return items

    def set_status(self, node_id: str, status: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            conn.execute("UPDATE node_trust SET status = ?, updated_at = ? WHERE node_id = ?", (status, round(time(), 3), node_id))
        return self.get(node_id)

    def verify_secret(self, node_id: str, secret: str) -> dict[str, Any]:
        item = self.get(node_id)
        if not item:
            return {"ok": False, "reason": "unknown_node", "node_id": node_id}
        if item.get("status") != "active":
            return {"ok": False, "reason": "node_not_active", "node_id": node_id, "status": item.get("status")}
        expected = str(item.get("secret_hash") or "")
        actual = hash_secret(secret)
        ok = hmac.compare_digest(expected, actual)
        return {"ok": ok, "reason": "valid" if ok else "bad_secret", "node_id": node_id, "trust_score": item.get("trust_score")}
