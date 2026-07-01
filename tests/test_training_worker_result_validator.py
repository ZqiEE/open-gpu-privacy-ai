from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from api.training_worker_result_validator import TrainingWorkerResultStore, build_training_worker_result, validate_training_worker_result


def real_training_job() -> dict:
    return {
        "id": "train-real-1",
        "type": "lora_micro",
        "payload": {
            "kind": "lora_micro",
            "name": "real-lora",
            "dataset_uri": "file:///tmp/train.jsonl",
            "base_model": "sshleifer/tiny-gpt2",
            "max_steps": 4,
            "real": True,
            "use_transformers": True,
            "peft": True,
            "lora": True,
            "requires_gpu": True,
            "allow_lightweight_fallback": False,
        },
    }


def gpu_profile() -> dict:
    return {
        "device_name": "gpu-worker",
        "cpu_threads": 16,
        "memory_gb": 64,
        "has_gpu": True,
        "gpu_name": "test-gpu",
    }


def real_training_output() -> dict:
    return {
        "name": "real-lora",
        "version": "local-v0",
        "source_job_id": "train-real-1",
        "location": "runtime_data/models/real-lora",
        "kind": "adapter",
        "status": "candidate",
        "metrics": {"backend": "lora", "score": 0.82},
        "notes": "local lora run finished",
        "training_runtime_evidence": {
            "schema_version": "ailovanta.training_runtime_evidence.v1",
            "requested_real_training": True,
            "requested_backend": "lora",
            "requires_gpu": True,
            "allow_lightweight_fallback": False,
            "actual_backend": "lora",
            "artifact_kind": "adapter",
            "real_training_executed": True,
            "fallback_used": False,
            "profile_has_gpu": True,
            "profile_gpu_name": "test-gpu",
            "torch_cuda_available": True,
            "cuda_device_count": 1,
            "cuda_devices": ["test-gpu"],
            "gpu_execution_evidence": True,
            "trained_rows": 8,
            "duration_seconds": 12.5,
        },
    }


def artifact_binding() -> dict:
    return {
        "binding_id": "binding-real-1",
        "model_key": "ailovanta-owned:candidate",
        "backend_kind": "transformers-local",
        "backend_ref": "file:///tmp/model",
        "artifact_hash": "sha256:" + "a" * 64,
        "status": "candidate",
        "metadata": {
            "source_job_id": "train-real-1",
            "artifact_distribution": {
                "artifact_id": "artifact-real-1",
                "model_artifact_hash": "sha256:" + "a" * 64,
                "storage_artifact_hash": "sha256:" + "b" * 64,
                "manifest_hash": "sha256:" + "c" * 64,
                "manifest_uri": "file:///tmp/manifest.json",
                "sealed": True,
            },
        },
    }


def test_training_worker_result_receipt_passes_real_gpu_training(tmp_path) -> None:
    worker_result = build_training_worker_result(
        job=real_training_job(),
        node_id="node-gpu-1",
        profile=gpu_profile(),
        output=real_training_output(),
        binding=artifact_binding(),
    )

    receipt = validate_training_worker_result(worker_result, store=TrainingWorkerResultStore(tmp_path / "training_receipts.sqlite3"))

    assert receipt["passed"] is True
    assert receipt["score"] == 1.0
    assert receipt["artifact_hash"] == artifact_binding()["artifact_hash"]
    assert receipt["result_hash"].startswith("sha256:")
    assert receipt["receipt_hash"].startswith("sha256:")


def test_training_worker_result_blocks_unproven_gpu_execution(tmp_path) -> None:
    output = real_training_output()
    output["training_runtime_evidence"] = {**output["training_runtime_evidence"], "gpu_execution_evidence": False, "torch_cuda_available": False}
    worker_result = build_training_worker_result(job=real_training_job(), node_id="node-gpu-1", profile=gpu_profile(), output=output, binding=artifact_binding())

    receipt = validate_training_worker_result(worker_result, store=TrainingWorkerResultStore(tmp_path / "training_receipts.sqlite3"))

    assert receipt["passed"] is False
    assert "runtime_evidence:gpu_execution_unproven" in receipt["blockers"]


def test_training_worker_result_validation_api(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AILOVANTA_TRAINING_WORKER_RESULT_PATH", str(tmp_path / "training_receipts.sqlite3"))
    worker_result = build_training_worker_result(job=real_training_job(), node_id="node-gpu-api", profile=gpu_profile(), output=real_training_output(), binding=artifact_binding())

    response = TestClient(app).post("/training/worker-results/validate", json={"worker_result": worker_result})

    assert response.status_code == 200
    body = response.json()
    assert body["receipt"]["passed"] is True

    listed = TestClient(app).get("/training/worker-results/validations", params={"job_id": "train-real-1"})
    assert listed.status_code == 200
    assert listed.json()["receipts"][0]["receipt_id"] == body["receipt"]["receipt_id"]
