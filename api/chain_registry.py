from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from api.sqlite_utils import connect_sqlite

CHAIN_EVENT_SCHEMA = "ailovanta.chain_event.v1"


class ChainRegistry:
    """Local chain-style registry for Ailovanta model identity events.

    This is a deterministic append-only ledger interface that can later be
    mirrored to a public blockchain or smart contract.
    """

    def __init__(self, path: str | Path = "runtime_data/chain_registry.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS chain_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    artifact_hash TEXT NOT NULL,
                    runtime_manifest_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    previous_event_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL,
                    anchor_status TEXT NOT NULL DEFAULT 'local_pending',
                    chain_tx TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def last_event_hash(self) -> str:
        with self.connect() as conn:
            row = conn.execute("SELECT event_hash FROM chain_events ORDER BY created_at DESC LIMIT 1").fetchone()
        return row[0] if row else "genesis"

    def append_model_event(self, payload: dict[str, Any]) -> dict:
        event_id = payload.get("event_id") or "chain_evt_" + uuid4().hex[:12]
        event = {
            "schema_version": CHAIN_EVENT_SCHEMA,
            "event_id": event_id,
            "event_type": payload.get("event_type", "model_artifact_promoted"),
            "model_id": payload["model_id"],
            "version": payload["version"],
            "artifact_hash": payload["artifact_hash"],
            "runtime_manifest_hash": payload["runtime_manifest_hash"],
            "previous_event_hash": self.last_event_hash(),
            "metadata": payload.get("metadata", {}),
        }
        event["event_hash"] = self._hash_event(event)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO chain_events (
                    event_id, event_type, model_id, version, artifact_hash,
                    runtime_manifest_hash, payload_json, previous_event_hash,
                    event_hash, anchor_status, chain_tx
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["event_id"],
                    event["event_type"],
                    event["model_id"],
                    event["version"],
                    event["artifact_hash"],
                    event["runtime_manifest_hash"],
                    json.dumps(event, ensure_ascii=False, sort_keys=True),
                    event["previous_event_hash"],
                    event["event_hash"],
                    payload.get("anchor_status", "local_pending"),
                    payload.get("chain_tx", ""),
                ),
            )
        return self.get_event(event_id) or {}

    def get_event(self, event_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM chain_events WHERE event_id = ?", (event_id,)).fetchone()
        return self._api_event(dict(row)) if row else None

    def latest_model_event(
        self,
        model_id: str,
        version: str,
        artifact_hash: str,
        runtime_manifest_hash: str,
        event_type: str = "model_artifact_promoted",
    ) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM chain_events
                WHERE model_id = ?
                  AND version = ?
                  AND artifact_hash = ?
                  AND runtime_manifest_hash = ?
                  AND event_type = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (model_id, version, artifact_hash, runtime_manifest_hash, event_type),
            ).fetchone()
        return self._api_event(dict(row)) if row else None

    def mark_anchored(self, event_id: str, chain_tx: str, anchor_receipt: dict[str, Any] | None = None, anchor_status: str = "anchored") -> dict | None:
        event = self.get_event(event_id)
        if not event:
            return None
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if anchor_receipt:
            metadata["anchor_receipt"] = anchor_receipt
        payload["metadata"] = metadata
        with self.connect() as conn:
            conn.execute(
                "UPDATE chain_events SET anchor_status = ?, chain_tx = ?, payload_json = ? WHERE event_id = ?",
                (anchor_status, chain_tx, json.dumps(payload, ensure_ascii=False, sort_keys=True), event_id),
            )
        return self.get_event(event_id)

    def list_events(self, limit: int = 100) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM chain_events ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._api_event(dict(row)) for row in rows]

    @staticmethod
    def _hash_event(event: dict[str, Any]) -> str:
        raw = json.dumps(event, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return "sha256:" + hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _api_event(row: dict) -> dict:
        payload = json.loads(row.pop("payload_json") or "{}")
        row["payload"] = payload
        row["metadata"] = payload.get("metadata", {})
        return row
