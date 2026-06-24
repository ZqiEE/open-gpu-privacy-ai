from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import uuid4

from api.sqlite_utils import connect_sqlite


class ModelNodeInventory:
    def __init__(self, path: str | Path = "runtime_data/model_registry.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS model_nodes (
                    inventory_id TEXT PRIMARY KEY,
                    node_id TEXT NOT NULL,
                    package_hash TEXT NOT NULL,
                    runtime TEXT NOT NULL,
                    memory_gb REAL NOT NULL,
                    has_gpu INTEGER NOT NULL,
                    health_score REAL NOT NULL DEFAULT 1.0,
                    status TEXT NOT NULL DEFAULT 'online',
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(node_id, package_hash)
                );
                """
            )

    def upsert_node_package(self, node_id: str, package_hash: str, runtime: str, memory_gb: float, has_gpu: bool, health_score: float = 1.0, status: str = "online") -> dict:
        inventory_id = "inv_" + uuid4().hex[:12]
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO model_nodes (inventory_id, node_id, package_hash, runtime, memory_gb, has_gpu, health_score, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(node_id, package_hash) DO UPDATE SET
                    runtime = excluded.runtime,
                    memory_gb = excluded.memory_gb,
                    has_gpu = excluded.has_gpu,
                    health_score = excluded.health_score,
                    status = excluded.status,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (inventory_id, node_id, package_hash, runtime, memory_gb, 1 if has_gpu else 0, health_score, status),
            )
        return self.get_node_package(node_id, package_hash) or {}

    def get_node_package(self, node_id: str, package_hash: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM model_nodes WHERE node_id = ? AND package_hash = ?", (node_id, package_hash)).fetchone()
        return self._row(dict(row)) if row else None

    def nodes_for_package(self, package_hash: str, online_only: bool = True) -> list[dict]:
        query = "SELECT * FROM model_nodes WHERE package_hash = ?"
        args: list = [package_hash]
        if online_only:
            query += " AND status = 'online'"
        query += " ORDER BY health_score DESC, memory_gb DESC"
        with self.connect() as conn:
            rows = conn.execute(query, args).fetchall()
        return [self._row(dict(row)) for row in rows]

    def list_inventory(self, limit: int = 100) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM model_nodes ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._row(dict(row)) for row in rows]

    def summary(self) -> dict:
        with self.connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS entries, COUNT(DISTINCT node_id) AS nodes, COUNT(DISTINCT package_hash) AS packages FROM model_nodes").fetchone()
        return {"entries": row["entries"], "nodes": row["nodes"], "packages": row["packages"]}

    @staticmethod
    def _row(item: dict) -> dict:
        item["has_gpu"] = bool(item["has_gpu"])
        return item
