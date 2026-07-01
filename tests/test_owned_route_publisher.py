from __future__ import annotations

import json
from pathlib import Path

from api.artifact_binding import ArtifactBindingStore
from api.owned_route_publisher import publish_owned_route_if_active
from api.route_book import RouteBook
from api.training_artifact_binding import bind_local_training_artifact


class FakeWarmer:
    def __init__(self, ok: bool = True) -> None:
        self.ok = ok
        self.calls = []

    def run(self, spec):
        self.calls.append(spec)
        if not self.ok:
            return {"ok": False, "reason": "fake_warm_failed"}
        return {"ok": True, "spec": {"model_key": spec.model_key, "runtime_id": spec.runtime_id, "node_id": spec.node_id}}


def test_publish_owned_route_requires_active_gate_ok(tmp_path: Path) -> None:
    bindings = ArtifactBindingStore(tmp_path / "bindings.sqlite3")
    artifact = tmp_path / "model.bin"
    artifact.write_bytes(b"model")
    binding = bindings.register_binding(
        {"model_id": "ailovanta-owned", "version": "candidate", "manifest_hash": "sha256:runtime"},
        {"artifact_id": "artifact-1", "artifact_hash": "sha256:" + "a" * 64, "checkpoint_uri": artifact.resolve().as_uri()},
        backend_kind="checkpoint-artifact",
        backend_ref=artifact.resolve().as_uri(),
        status="candidate",
        metadata={"promotion_gate": {"ok": True, "decision": "promote_active", "blockers": []}},
    )

    result = publish_owned_route_if_active(binding, routes=RouteBook(tmp_path / "routes.sqlite3"), bindings=bindings, warmer=FakeWarmer())

    assert result["ok"] is False
    assert result["reason"] == "binding_not_active"


def test_publish_owned_route_sets_route_for_active_binding(tmp_path: Path) -> None:
    bindings = ArtifactBindingStore(tmp_path / "bindings.sqlite3")
    routes = RouteBook(tmp_path / "routes.sqlite3")
    warmer = FakeWarmer()
    artifact = tmp_path / "model.bin"
    artifact.write_bytes(b"model")
    binding = bindings.register_binding(
        {"model_id": "ailovanta-owned", "version": "candidate", "manifest_hash": "sha256:runtime"},
        {"artifact_id": "artifact-1", "artifact_hash": "sha256:" + "a" * 64, "checkpoint_uri": artifact.resolve().as_uri()},
        backend_kind="checkpoint-artifact",
        backend_ref=artifact.resolve().as_uri(),
        status="active",
        metadata={"promotion_gate": {"ok": True, "decision": "promote_active", "blockers": []}},
    )

    result = publish_owned_route_if_active(binding, routes=routes, bindings=bindings, warmer=warmer)

    assert result["ok"] is True
    assert routes.active("owned-chat/default")["binding_id"] == binding["binding_id"]
    assert warmer.calls[0].model_key == "ailovanta-owned:candidate"


def test_training_artifact_binding_records_route_publish_metadata(tmp_path: Path, monkeypatch) -> None:
    dataset = tmp_path / "train.jsonl"
    dataset.write_text(json.dumps({"text": "def add(left, right):\n    return left + right", "record_kind": "code"}) + "\n", encoding="utf-8")
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "ngram_model.json").write_text(
        json.dumps(
            {
                "schema": "ailovanta.lightweight_ngram.v1",
                "base_model": "local",
                "dataset_path": str(dataset),
                "rows": 1,
                "transitions": 1,
                "train_loss": 1.0,
                "counts": {"\n": {"d": 1}},
            }
        ),
        encoding="utf-8",
    )
    store = ArtifactBindingStore(tmp_path / "bindings.sqlite3")

    monkeypatch.setattr("api.training_artifact_binding.evaluate_training_artifact_binding", lambda *_args, **_kwargs: {"ok": True, "decision": "promote_active", "blockers": []})
    monkeypatch.setattr(
        "api.training_artifact_binding.publish_owned_route_if_active",
        lambda binding, **_kwargs: {"ok": True, "reason": "published", "route": {"route_key": "owned-chat/default", "model_key": binding["model_key"], "binding_id": binding["binding_id"], "status": "active"}},
    )

    binding = bind_local_training_artifact(
        {"source_job_id": "job-route-publish", "location": str(model_dir), "metrics": {"backend": "lightweight-ngram"}, "status": "candidate"},
        store,
        manifest_dir=tmp_path / "artifact_manifests",
        replica_book_path=tmp_path / "replica_book.json",
        replica_tasks_path=tmp_path / "replica_repair_tasks.json",
        replica_storage_root=tmp_path / "storage_replicas",
    )

    assert binding["status"] == "active"
    assert binding["metadata"]["route_publish"]["ok"] is True
    assert binding["metadata"]["route_publish"]["route_key"] == "owned-chat/default"
