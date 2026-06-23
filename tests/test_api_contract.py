from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app, store
from api.storage import SchedulerStore


def test_root_contract() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Ailovanta"
    assert "scheduler" in body


def test_register_node_and_job_flow() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        local_store = SchedulerStore(Path(tmp) / "scheduler.sqlite3")
        original_path = store.path
        store.path = local_store.path
        try:
            client = TestClient(app)
            node = client.post(
                "/nodes/register",
                json={
                    "device_name": "pytest-node",
                    "cpu_threads": 4,
                    "memory_gb": 8,
                    "has_gpu": False,
                    "gpu_name": None,
                    "contribution_percent": 30,
                },
            )
            assert node.status_code == 200
            node_id = node.json()["node_id"]

            job = client.get("/jobs/next", params={"node_id": node_id})
            assert job.status_code == 200
            payload = job.json()["job"]
            assert payload is not None

            result = client.post(
                "/jobs/result",
                json={
                    "node_id": node_id,
                    "job_id": payload["id"],
                    "status": "ok",
                    "output_summary": "simulated pytest result",
                },
            )
            assert result.status_code == 200
            body = result.json()
            assert body["ok"] is True
            assert "verification" in body

            status = client.get("/network/status")
            assert status.status_code == 200
            assert "nodes" in status.json()

            verification = client.get("/verification/status")
            assert verification.status_code == 200
            assert "pass_rate" in verification.json()
        finally:
            store.path = original_path


def test_training_job_and_model_version() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        local_store = SchedulerStore(Path(tmp) / "scheduler.sqlite3")
        original_path = store.path
        store.path = local_store.path
        try:
            client = TestClient(app)
            job = client.post(
                "/training/jobs",
                json={
                    "kind": "rag_import",
                    "name": "pytest-rag",
                    "dataset_uri": "file://pytest/docs",
                    "base_model": "qwen2.5:3b",
                },
            )
            assert job.status_code == 200
            job_id = job.json()["job"]["id"]

            training_jobs = client.get("/training/jobs")
            assert training_jobs.status_code == 200
            assert any(item["id"] == job_id for item in training_jobs.json()["jobs"])

            model = client.post(
                "/models/versions",
                json={
                    "name": "pytest-model",
                    "base_model": "qwen2.5:3b",
                    "source_job_id": job_id,
                },
            )
            assert model.status_code == 200
            assert model.json()["model"]["source_job_id"] == job_id
        finally:
            store.path = original_path
