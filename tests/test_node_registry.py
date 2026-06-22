from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app, store
from api.storage import SchedulerStore


def test_register_existing_node_id_reuses_record() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        local_store = SchedulerStore(Path(tmp) / "scheduler.sqlite3")
        original_path = store.path
        store.path = local_store.path
        try:
            client = TestClient(app)
            payload = {
                "node_id": "node_pytest_identity",
                "device_name": "identity-node",
                "cpu_threads": 4,
                "memory_gb": 8,
                "has_gpu": False,
                "gpu_name": None,
                "contribution_percent": 30,
            }
            first = client.post("/nodes/register", json=payload)
            second = client.post("/nodes/register", json=payload | {"memory_gb": 16})
            assert first.status_code == 200
            assert second.status_code == 200
            assert second.json()["node_id"] == "node_pytest_identity"
            nodes = client.get("/nodes")
            assert nodes.status_code == 200
        finally:
            store.path = original_path
