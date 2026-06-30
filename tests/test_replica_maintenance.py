import json
from pathlib import Path

from api.chunk_manifest import build_manifest, manifest_hash
from api.replica_book import add_manifest, status as replica_status
from api.replica_maintenance import run_replica_maintenance_once


def test_replica_maintenance_repairs_local_chunks(tmp_path: Path) -> None:
    artifact = tmp_path / "model.bin"
    artifact.write_bytes(b"chunk-one|chunk-two|chunk-three")
    manifest = build_manifest(artifact, chunk_size=10, min_replicas=2, sources=["file://" + str(artifact)])
    manifest["artifact_id"] = "artifact-maintenance"
    manifest["manifest_hash"] = manifest_hash(manifest)
    book_path = tmp_path / "replica_book.json"
    add_manifest(manifest, node_id="storage-1", location="file://" + str(artifact), path=book_path)

    result = run_replica_maintenance_once(
        tasks_path=tmp_path / "repairs.json",
        replica_book_path=book_path,
        storage_root=tmp_path / "storage_replicas",
    )

    assert result["ok"] is True
    assert result["planned"]["created_count"] == len(manifest["chunks"])
    assert result["completed_count"] == len(manifest["chunks"])
    assert result["failed_count"] == 0
    assert replica_status(book_path)["artifacts"][0]["healthy"] is True
    for completed in result["completed"]:
        target = Path(completed["target"])
        assert target.exists()
        assert target.read_bytes()


def test_full_auto_status_reports_replica_repairs(tmp_path: Path, monkeypatch, capsys) -> None:
    import scripts.show_full_auto_status as status_script

    monkeypatch.setattr(status_script, "ROOT", tmp_path)
    runtime = tmp_path / "runtime_data"
    runtime.mkdir()
    (runtime / "full_auto_state.json").write_text(json.dumps({"ok": True, "replica_maintenance_pid": 123}), encoding="utf-8")
    repairs = {
        "schema_version": "ailovanta.replica_repair_tasks.v1",
        "tasks": {
            "repair-1": {"task_id": "repair-1", "status": "queued", "updated_at": 1},
            "repair-2": {"task_id": "repair-2", "status": "done", "updated_at": 2},
        },
    }
    (runtime / "replica_repair_tasks.json").write_text(json.dumps(repairs), encoding="utf-8")

    assert status_script.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["replica_repairs"]["queued"] == 1
    assert payload["replica_repairs"]["done"] == 1


def test_replica_maintenance_does_not_complete_external_targets(tmp_path: Path) -> None:
    artifact = tmp_path / "model.bin"
    artifact.write_bytes(b"owned-model")
    manifest = build_manifest(artifact, min_replicas=2, sources=["file://" + str(artifact)])
    book_path = tmp_path / "replica_book.json"
    add_manifest(manifest, node_id="storage-1", location="file://" + str(artifact), path=book_path)

    result = run_replica_maintenance_once(
        tasks_path=tmp_path / "repairs.json",
        replica_book_path=book_path,
        storage_root=tmp_path / "storage_replicas",
        target_nodes=["external-storage-2"],
    )

    assert result["ok"] is True
    assert result["planned"]["created_count"] == 1
    assert result["completed_count"] == 0
    assert result["skipped_count"] == 1
    assert result["skipped"][0]["reason"] == "non_local_target"
    assert replica_status(book_path)["artifacts"][0]["healthy"] is False
