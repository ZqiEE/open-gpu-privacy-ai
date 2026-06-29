import json
from pathlib import Path

from api.artifact_binding import ArtifactBindingStore
from api.chunk_manifest import build_manifest, manifest_hash
from api.owned_doctor import OwnedDoctor
from api.replica_book import add_manifest
from api.route_book import RouteBook
from api.route_health import RouteHealth
from api.runtime_router import ModelManifest, RuntimeNodeProfile
from api.runtime_store import RuntimeStore


def _ready_checker(tmp_path: Path, distribution: dict | None = None) -> tuple[RouteHealth, dict, Path]:
    checkpoint = tmp_path / "checkpoint.bin"
    checkpoint.write_bytes(b"owned-trained-checkpoint")

    routes = RouteBook(tmp_path / "routes.sqlite3")
    bindings = ArtifactBindingStore(tmp_path / "bindings.sqlite3")
    runtime = RuntimeStore(tmp_path / "runtime.sqlite3")
    model = ModelManifest(model_id="ailovanta-owned", version="candidate", manifest_hash="runtime-manifest-hash")
    runtime.register_model(model)
    runtime.register_runtime(
        RuntimeNodeProfile(
            runtime_id="rt-1",
            node_id="node-1",
            pool="trusted_runtime_pool",
            cached_models=[model.key],
            supported_engines=["checkpoint-artifact"],
        )
    )
    artifact = {
        "artifact_id": "artifact-model-record",
        "artifact_hash": "sha256:model-artifact-record",
        "checkpoint_uri": "file://" + str(checkpoint),
    }
    binding = bindings.register_binding(
        runtime_model=runtime.get_model(model.key),
        artifact=artifact,
        backend_ref="file://" + str(checkpoint),
        status="active",
        metadata={"artifact_distribution": distribution} if distribution else {},
    )
    routes.set_active("owned-chat/default", model.key, binding_id=binding["binding_id"])
    checker = RouteHealth(
        routes=routes,
        bindings=bindings,
        doctor=OwnedDoctor(bindings=bindings, runtime=runtime),
        replica_book_path=tmp_path / "replica_book.json",
    )
    return checker, binding, checkpoint


def _distribution(tmp_path: Path, checkpoint: Path, min_replicas: int = 1) -> dict:
    manifest = build_manifest(checkpoint, min_replicas=min_replicas, sources=["node://storage-1/checkpoint.bin"])
    manifest["artifact_id"] = "artifact-model-record"
    manifest["manifest_hash"] = manifest_hash(manifest)
    manifest_path = tmp_path / "artifact_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    add_manifest(manifest, node_id="storage-1", location="file://" + str(checkpoint), path=tmp_path / "replica_book.json")
    return {
        "schema_version": "ailovanta.artifact_distribution.v1",
        "artifact_id": "artifact-model-record",
        "model_artifact_hash": "sha256:model-artifact-record",
        "storage_artifact_hash": manifest["artifact_hash"],
        "manifest_hash": manifest["manifest_hash"],
        "manifest_uri": "file://" + str(manifest_path),
        "replica_book_path": str(tmp_path / "replica_book.json"),
    }


def test_route_health_distribution_gate_passes_with_manifest_and_replicas(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.bin"
    checkpoint.write_bytes(b"owned-trained-checkpoint")
    distribution = _distribution(tmp_path, checkpoint, min_replicas=1)
    checker, _, _ = _ready_checker(tmp_path, distribution)

    result = checker.check("owned-chat/default", verify_distribution=True)

    assert result["ok"] is True
    assert result["artifact_distribution"]["ok"] is True
    assert result["artifact_distribution"]["replica_artifact"]["healthy"] is True


def test_route_health_distribution_gate_blocks_missing_distribution(tmp_path: Path) -> None:
    checker, _, _ = _ready_checker(tmp_path)

    result = checker.check("owned-chat/default", verify_distribution=True)

    assert result["ok"] is False
    assert "artifact_distribution:missing_artifact_distribution" in result["blockers"]


def test_route_health_distribution_gate_blocks_under_replicated_artifact(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.bin"
    checkpoint.write_bytes(b"owned-trained-checkpoint")
    distribution = _distribution(tmp_path, checkpoint, min_replicas=2)
    checker, _, _ = _ready_checker(tmp_path, distribution)

    result = checker.check("owned-chat/default", verify_distribution=True)

    assert result["ok"] is False
    assert "artifact_distribution:replica_book_under_replicated" in result["blockers"]
