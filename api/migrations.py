from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from api.sqlite_utils import connect_sqlite


MIGRATIONS: list[tuple[str, str]] = [
    (
        "001_runtime_ops_tables",
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            name TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS node_reputation_events (
            event_id TEXT PRIMARY KEY,
            node_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            delta REAL NOT NULL,
            reason TEXT NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS queue_limits (
            name TEXT PRIMARY KEY,
            max_queued INTEGER NOT NULL DEFAULT 1000,
            max_assigned INTEGER NOT NULL DEFAULT 100,
            max_per_node_assigned INTEGER NOT NULL DEFAULT 3,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS artifact_versions (
            artifact_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            version TEXT NOT NULL,
            location TEXT NOT NULL,
            catalog_item_id TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            previous_artifact_id TEXT,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS app_events (
            event_id TEXT PRIMARY KEY,
            level TEXT NOT NULL,
            source TEXT NOT NULL,
            message TEXT NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """,
    )
]


class MigrationRunner:
    def __init__(self, path: str | Path = "runtime_data/scheduler.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def applied(self) -> set[str]:
        with self.connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
            rows = conn.execute("SELECT name FROM schema_migrations").fetchall()
        return {row["name"] for row in rows}

    def run(self) -> dict[str, Any]:
        done = self.applied()
        applied_now: list[str] = []
        with self.connect() as conn:
            for name, sql in MIGRATIONS:
                if name in done:
                    continue
                conn.executescript(sql)
                conn.execute("INSERT OR IGNORE INTO schema_migrations (name) VALUES (?)", (name,))
                applied_now.append(name)
        return {"ok": True, "applied": applied_now, "available": [name for name, _ in MIGRATIONS]}

    def status(self) -> dict[str, Any]:
        done = self.applied()
        return {"applied": sorted(done), "pending": [name for name, _ in MIGRATIONS if name not in done]}
