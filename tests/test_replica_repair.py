import json
from pathlib import Path

from api.chunk_manifest import build_manifest, manifest_hash
from api.replica_book import add_manifest, status as replica_status
from api.replica_repair import ReplicaRepairStore
from api.route_health import RouteHealth
from tests.test_route_health_distribution import _ready_checker


def _under_replicated_manifest(tmp_path: Path) -> tuple[dict, Path]:
    artifact = tmp_path / "checkpoint.bin"
    artifact.write_bytes(b"owned-checkpoint")
    manifest = build_manifest(artifact, min_replicas=2, sources=["node://storage-1/checkpoint.bin"])
    manifest["artifact_id"] = "artifact-model-record"
    manifest["manifest_hash"] = manifest_hash(manifest)
    manifest_path = tmp_path / "artifact.manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    add_manifest(manifest, node_id="storage-1", location="file://" + str(artifact), path=tmp_path / "replica_book.json")
    return manifest, manifest_path


def test_replica_repair_plans_idempotent_tasks_and_completes_copy(tmp_path: Path) -> None:
    manifest, _ = _under_replicated_manifest(tmp_path)
    store = ReplicaRepairStore(path=tmp_path / "repairs.json", replica_book_path=tmp_path / "replica_book.json")

    planned = store.plan_repairs(target_nodes=["storage-2"])
    planned_again = store.plan_repairs(target_nodes=["storage-2"])

    assert planned["created_count"] == 1
    assert planned_again["created_count"] == 0
    task = planned["tasks"][0]
    assert task["payload"]["artifact_hash"] == manifest["artifact_hash"]
    assert task["payload"]["target_node_id"] == "storage-2"

    completed = store.complete(task["task_id"])

    assert completed["ok"] is True
    assert completed["task"]["status"] == "done"
    assert replica_status(tmp_path / "replica_book.json")["artifacts"][0]["healthy"] is True


def test_replica_repair_turns_distribution_gate_green(tmp_path: Path) -> None:
    manifest, manifest_path = _under_replicated_manifest(tmp_path)
    distribution = {
        "schema_version": "ailovanta.artifact_distribution.v1",
        "artifact_id": "artifact-model-record",
        "model_artifact_hash": "sha256:model-artifact-record",
        "storage_artifact_hash": manifest["artifact_hash"],
        "manifest_hash": manifest["manifest_hash"],
        "manifest_uri": "file://" + str(manifest_path),
        "replica_book_path": str(tmp_path / "replica_book.json"),
    }
    checker, _, _ = _ready_checker(tmp_path, distribution)
    before = checker.check("owned-chat/default", verify_distribution=True)
    assert before["ok"] is False

    store = ReplicaRepairStore(path=tmp_path / "repairs.json", replica_book_path=tmp_path / "replica_book.json")
    task = store.plan_repairs(target_nodes=["storage-2"])["tasks"][0]
    store.complete(task["task_id"])

    after = checker.check("owned-chat/default", verify_distribution=True)
    assert after["ok"] is True
    assert after["artifact_distribution"]["replica_artifact"]["healthy"] is True


def test_route_exposes_replica_repair_api() -> None:
    from api.main import app

    paths = {route.path for route in app.routes}
    assert "/replicas/repair/plan" in paths
    assert "/replicas/repair/tasks" in paths
