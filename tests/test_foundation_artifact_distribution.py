import json
from pathlib import Path

from api.artifact_binding import ArtifactBindingStore
from api.chain_registry import ChainRegistry
from api.core_result_store import CoreResultStore
from api.foundation_result_import import import_foundation_result
from api.replica_book import status as replica_status
from api.runtime_store import RuntimeStore


def test_import_foundation_result_prepares_artifact_distribution(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.bin"
    checkpoint.write_bytes(b"trained-checkpoint-bytes")

    result = import_foundation_result(
        {
            "plan": {"plan_id": "plan_1", "model": {"model_id": "ailovanta-owned"}},
            "artifact": {
                "artifact_id": "artifact_1",
                "artifact_hash": "sha256:model-artifact-record",
                "model_id": "ailovanta-owned",
                "version": "candidate",
                "source_plan_id": "plan_1",
                "checkpoint_uri": "file://" + str(checkpoint),
                "backend_kind": "checkpoint-artifact",
                "backend_ref": "file://" + str(checkpoint),
            },
        },
        core_results=CoreResultStore(tmp_path / "core.sqlite3"),
        runtime_store=RuntimeStore(tmp_path / "runtime.sqlite3"),
        chain_registry=ChainRegistry(tmp_path / "chain.sqlite3"),
        binding_store=ArtifactBindingStore(tmp_path / "bindings.sqlite3"),
        artifact_manifest_dir=tmp_path / "artifact_manifests",
        replica_book_path=tmp_path / "replica_book.json",
        storage_node_id="storage-node-1",
    )

    distribution = result["artifact_distribution"]
    assert distribution["schema_version"] == "ailovanta.artifact_distribution.v1"
    assert distribution["model_artifact_hash"] == "sha256:model-artifact-record"
    assert distribution["storage_artifact_hash"].startswith("sha256:")
    assert distribution["storage_artifact_hash"] != distribution["model_artifact_hash"]
    assert distribution["hash_matches_model_artifact"] is False
    assert Path(distribution["manifest_uri"].removeprefix("file://")).exists()

    manifest = json.loads(Path(distribution["manifest_uri"].removeprefix("file://")).read_text(encoding="utf-8"))
    assert manifest["manifest_hash"] == distribution["manifest_hash"]
    assert manifest["chunks"][0]["sources"] == ["node://storage-node-1/checkpoint.bin"]

    book_status = replica_status(tmp_path / "replica_book.json")
    assert book_status["artifact_count"] == 1
    assert book_status["artifacts"][0]["healthy"] is False

    binding_meta = result["artifact_binding"]["metadata"]
    assert binding_meta["artifact_distribution"]["manifest_hash"] == distribution["manifest_hash"]
    assert "artifact_manifest" not in binding_meta

    chain_meta = result["chain_event"]["metadata"]
    assert chain_meta["artifact_distribution"]["storage_artifact_hash"] == distribution["storage_artifact_hash"]
