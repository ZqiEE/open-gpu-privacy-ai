from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4


class DistributedModelRegistry:
    def __init__(self, path: str | Path = "runtime_data/model_registry.sqlite3") -> None:
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
                CREATE TABLE IF NOT EXISTS model_packages (
                    package_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    base TEXT NOT NULL,
                    package_hash TEXT NOT NULL,
                    adapter_hash TEXT NOT NULL,
                    data_hash TEXT NOT NULL,
                    score REAL NOT NULL,
                    object_ref TEXT NOT NULL,
                    runtime TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'available',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(package_hash)
                );
                """
            )

    def register(self, package: dict[str, Any], status: str = "available") -> dict:
        package_id = "pkg_" + uuid4().hex[:12]
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO model_packages (
                    package_id, name, version, base, package_hash, adapter_hash, data_hash,
                    score, object_ref, runtime, tags_json, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    package_id,
                    package["name"],
                    package["version"],
                    package["base"],
                    package["package_hash"],
                    package["adapter_hash"],
                    package["data_hash"],
                    package["score"],
                    package["object_ref"],
                    package["runtime"],
                    json.dumps(package.get("tags", []), ensure_ascii=False),
                    status,
                ),
            )
        return self.get_by_hash(package["package_hash"]) or {}

    def get_by_hash(self, package_hash: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM model_packages WHERE package_hash = ?", (package_hash,)).fetchone()
        return self._row(dict(row)) if row else None

    def list_packages(self, min_score: float | None = None, tag: str | None = None, limit: int = 100) -> list[dict]:
        packages = self._list_all(limit=limit)
        if min_score is not None:
            packages = [item for item in packages if item["score"] >= min_score]
        if tag:
            packages = [item for item in packages if tag in item.get("tags", [])]
        return packages[:limit]

    def best_package(self, tag: str | None = None) -> dict | None:
        packages = self.list_packages(tag=tag, limit=1000)
        if not packages:
            return None
        return sorted(packages, key=lambda item: item["score"], reverse=True)[0]

    def summary(self) -> dict:
        with self.connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS packages, COALESCE(AVG(score), 0) AS avg_score, COALESCE(MAX(score), 0) AS best_score FROM model_packages").fetchone()
        return {"packages": row["packages"], "average_score": round(row["avg_score"], 3), "best_score": round(row["best_score"], 3)}

    def _list_all(self, limit: int = 100) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM model_packages ORDER BY score DESC, created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._row(dict(row)) for row in rows]

    @staticmethod
    def _row(item: dict) -> dict:
        item["tags"] = json.loads(item.pop("tags_json") or "[]")
        return item
