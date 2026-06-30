from pathlib import Path

from fastapi.testclient import TestClient

from api.chunk_manifest import build_manifest
from api.main import app
from api.reputation_ops import ReputationOps
from api.storage import SchedulerStore
from api.worker_result_validator import WorkerResultValidationStore, validate_worker_result


def worker_result() -> dict:
    return {
        "answer": "owned worker answer",
        "source": "artifact-bound-checkpoint",
        "model_id": "ailovanta-owned",
        "version": "candidate",
        "runtime_id": "runtime-1",
        "node_id": "node-validator-1",
        "model_manifest_hash": "sha256:runtime",
        "artifact_binding": {
            "binding_id": "binding-1",
            "runtime_manifest_hash": "sha256:runtime",
            "artifact_hash": "sha256:artifact",
            "backend_kind": "checkpoint-artifact",
        },
    }


def artifact_manifest(tmp_path: Path) -> dict:
    artifact = tmp_path / "checkpoint.bin"
    artifact.write_bytes(b"abcdefghi")
    manifest = build_manifest(artifact, chunk_size=3, sources=["node://node-validator-1/checkpoint.bin"], min_replicas=1)
    return {**manifest, "artifact_hash": "sha256:artifact"}


def test_validate_worker_result_records_receipt_and_reputation(tmp_path: Path) -> None:
    scheduler = SchedulerStore(tmp_path / "scheduler.sqlite3")
    scheduler.register_node(
        {
            "node_id": "node-validator-1",
            "device_name": "validator",
            "cpu_threads": 8,
            "memory_gb": 16,
            "has_gpu": True,
            "gpu_name": "test",
            "contribution_percent": 30,
        }
    )

    receipt = validate_worker_result(
        worker_result(),
        artifact_manifest=artifact_manifest(tmp_path),
        store=WorkerResultValidationStore(tmp_path / "validations.sqlite3"),
        reputation=ReputationOps(tmp_path / "scheduler.sqlite3"),
    )

    assert receipt["passed"] is True
    assert receipt["score"] == 1.0
    assert receipt["sampled_chunks"]
    assert receipt["reputation_event"]["event_type"] == "worker_result_validation"


def test_validate_worker_result_blocks_hash_mismatch(tmp_path: Path) -> None:
    bad = worker_result()
    bad["model_manifest_hash"] = "sha256:wrong"

    receipt = validate_worker_result(
        bad,
        artifact_manifest=artifact_manifest(tmp_path),
        store=WorkerResultValidationStore(tmp_path / "validations.sqlite3"),
        apply_reputation=False,
    )

    assert receipt["passed"] is False
    assert "runtime_manifest_hash_mismatch" in receipt["blockers"]


def test_worker_result_validation_api(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AILOVANTA_WORKER_VALIDATION_PATH", str(tmp_path / "validations.sqlite3"))

    response = TestClient(app).post(
        "/worker-results/validate",
        json={
            "worker_result": worker_result(),
            "artifact_manifest": artifact_manifest(tmp_path),
            "sample_size": 2,
            "apply_reputation": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["receipt"]["passed"] is True

    listed = TestClient(app).get("/worker-results/validations", params={"node_id": "node-validator-1"})
    assert listed.status_code == 200
    assert listed.json()["receipts"][0]["receipt_id"] == body["receipt"]["receipt_id"]
