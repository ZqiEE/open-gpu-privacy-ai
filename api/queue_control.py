from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from api.migrations import MigrationRunner
from api.sqlite_utils import connect_sqlite


class QueueControl:
    def __init__(self, path: str | Path = "runtime_data/scheduler.sqlite3") -> None:
        self.path = Path(path)
        MigrationRunner(path).run()
        self.ensure_default()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def ensure_default(self) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO queue_limits (name, max_queued, max_assigned, max_per_node_assigned) VALUES ('default', 1000, 100, 3)"
            )

    def limits(self) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM queue_limits WHERE name = 'default'").fetchone()
        return dict(row)

    def update(self, max_queued: int, max_assigned: int, max_per_node_assigned: int) -> dict[str, Any]:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO queue_limits (name, max_queued, max_assigned, max_per_node_assigned, updated_at)
                VALUES ('default', ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (max_queued, max_assigned, max_per_node_assigned),
            )
        return self.limits()

    def snapshot(self) -> dict[str, Any]:
        with self.connect() as conn:
            queued = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'queued'").fetchone()[0]
            assigned = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'assigned'").fetchone()[0]
            by_node = conn.execute("SELECT assigned_to AS node_id, COUNT(*) AS count FROM jobs WHERE status = 'assigned' AND assigned_to IS NOT NULL GROUP BY assigned_to ORDER BY count DESC").fetchall()
        limits = self.limits()
        return {"queued": queued, "assigned": assigned, "assigned_by_node": [dict(row) for row in by_node], "limits": limits, "throttled": queued >= limits["max_queued"] or assigned >= limits["max_assigned"]}

    def can_enqueue(self) -> dict[str, Any]:
        snap = self.snapshot()
        allowed = snap["queued"] < snap["limits"]["max_queued"]
        return {"allowed": allowed, **snap}

    def can_assign(self, node_id: str) -> dict[str, Any]:
        snap = self.snapshot()
        node_count = 0
        for item in snap["assigned_by_node"]:
            if item["node_id"] == node_id:
                node_count = item["count"]
        allowed = snap["assigned"] < snap["limits"]["max_assigned"] and node_count < snap["limits"]["max_per_node_assigned"]
        return {"allowed": allowed, "node_id": node_id, "node_assigned": node_count, **snap}
