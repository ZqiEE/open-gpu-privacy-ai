from __future__ import annotations

import tempfile
from pathlib import Path

from api.usage_store import UsageStore


def test_usage_store_records_and_summarizes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = UsageStore(Path(tmp) / "usage.sqlite3")
        event = store.record("local", "chat", 2.0, "pytest", {"mode": "test"})
        assert event["user_id"] == "local"
        assert event["event_type"] == "chat"
        summary = store.summary("local")
        assert summary["total_events"] == 1
        assert summary["by_type"]["chat"] == 2.0


def test_usage_store_lists_events() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = UsageStore(Path(tmp) / "usage.sqlite3")
        store.record("u1", "chat", 1, "pytest")
        store.record("u2", "training", 3, "pytest")
        assert len(store.list_events(limit=10)) == 2
        assert len(store.list_events(user_id="u1", limit=10)) == 1
