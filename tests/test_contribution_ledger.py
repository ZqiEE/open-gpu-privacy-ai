from __future__ import annotations

import tempfile
from pathlib import Path

from api.contribution_ledger import ContributionLedger


def test_ledger_appends_and_summarizes_events() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ledger = ContributionLedger(Path(tmp) / "ledger.sqlite3")
        event = ledger.append("node_a", "task_proof", "hash_a", 1.2, 12.0, {"ok": True})
        assert event["event_id"]
        assert event["details"]["ok"] is True
        assert ledger.node_summary("node_a")["credits"] == 12.0
        assert ledger.network_summary()["events"] == 1
