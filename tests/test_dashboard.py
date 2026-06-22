from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app, store
from api.storage import SchedulerStore


def test_dashboard_summary_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        local_store = SchedulerStore(Path(tmp) / "scheduler.sqlite3")
        original_path = store.path
        store.path = local_store.path
        try:
            client = TestClient(app)
            response = client.get("/dashboard/summary")
            assert response.status_code == 200
            body = response.json()
            assert "nodes" in body
            assert "total_jobs" in body
            assert "verification_pass_rate" in body
            assert body["store"] == "sqlite"
        finally:
            store.path = original_path


def test_dashboard_lists_contract() -> None:
    client = TestClient(app)
    jobs = client.get("/dashboard/jobs")
    assert jobs.status_code == 200
    assert "jobs" in jobs.json()

    models = client.get("/dashboard/models")
    assert models.status_code == 200
    assert "models" in models.json()
