import json
from pathlib import Path

from fastapi.testclient import TestClient

from api.artifact_binding import ArtifactBindingStore
from api.worker import app


def register_checkpoint_binding(tmp_path: Path, checkpoint: Path | None = None) -> dict:
    checkpoint_path = checkpoint or (tmp_path / "checkpoint.json")
    if checkpoint is None:
        checkpoint_path.write_bytes(
            json.dumps({"backend": "jsonl-stat", "token_count": 42, "train_loss": 0.2, "eval_loss": 0.3}).encode("utf-8")
        )
    store = ArtifactBindingStore(tmp_path / "bindings.sqlite3")
    return store.register_binding(
        {
            "model_id": "ailovanta-owned",
            "version": "candidate",
            "model_key": "ailovanta-owned:candidate",
            "manifest_hash": "sha256:manifest",
            "status": "active",
        },
        {
            "artifact_id": "artifact_1",
            "artifact_hash": "sha256:artifact",
            "checkpoint_uri": "file://" + str(checkpoint_path),
        },
        backend_kind="checkpoint-artifact",
        backend_ref="file://" + str(checkpoint_path),
        status="active",
    )


def infer_payload(manifest_hash: str = "sha256:manifest") -> dict:
    return {
        "prompt": "hello",
        "model_id": "ailovanta-owned",
        "version": "candidate",
        "runtime_id": "runtime-node-1",
        "node_id": "node-1",
        "model_manifest_hash": manifest_hash,
        "policy_mode": "open_research",
    }


def test_worker_uses_artifact_bound_checkpoint(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AILOVANTA_ARTIFACT_BINDINGS_PATH", str(tmp_path / "bindings.sqlite3"))
    register_checkpoint_binding(tmp_path)

    response = TestClient(app).post("/v1/owned/infer", json=infer_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "artifact-bound-checkpoint"
    assert body["artifact_binding"]["runtime_manifest_hash"] == "sha256:manifest"
    assert "Token count: 42" in body["answer"]


def test_worker_rejects_manifest_hash_mismatch(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AILOVANTA_ARTIFACT_BINDINGS_PATH", str(tmp_path / "bindings.sqlite3"))
    register_checkpoint_binding(tmp_path)

    response = TestClient(app).post("/v1/owned/infer", json=infer_payload("sha256:wrong"))

    assert response.status_code == 409
    assert response.json()["detail"]["reason"] == "model_manifest_hash_mismatch"


def test_worker_requires_artifact_binding_by_default(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AILOVANTA_ARTIFACT_BINDINGS_PATH", str(tmp_path / "bindings.sqlite3"))
    monkeypatch.delenv("AILOVANTA_WORKER_ALLOW_BOOTSTRAP_FALLBACK", raising=False)

    response = TestClient(app).post("/v1/owned/infer", json=infer_payload())

    assert response.status_code == 503
    assert response.json()["detail"]["reason"] == "missing_artifact_binding"


def test_worker_reports_unavailable_bound_runtime(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AILOVANTA_ARTIFACT_BINDINGS_PATH", str(tmp_path / "bindings.sqlite3"))
    register_checkpoint_binding(tmp_path, checkpoint=tmp_path / "missing.json")

    response = TestClient(app).post("/v1/owned/infer", json=infer_payload())

    assert response.status_code == 503
    assert response.json()["detail"]["reason"] == "artifact_bound_runtime_unavailable"
