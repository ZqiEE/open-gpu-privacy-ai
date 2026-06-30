from pathlib import Path

from api.artifact_binding import ArtifactBindingStore
from api.chain_registry import ChainRegistry
from api.owned_doctor import OwnedDoctor
from api.route_book import RouteBook
from api.route_health import RouteHealth
from api.runtime_router import ModelManifest, RuntimeNodeProfile
from api.runtime_store import RuntimeStore


def _ready_checker(tmp_path: Path) -> tuple[RouteHealth, dict, ChainRegistry]:
    checkpoint = tmp_path / "checkpoint.bin"
    checkpoint.write_bytes(b"owned-trained-checkpoint")
    routes = RouteBook(tmp_path / "routes.sqlite3")
    bindings = ArtifactBindingStore(tmp_path / "bindings.sqlite3")
    runtime = RuntimeStore(tmp_path / "runtime.sqlite3")
    chain = ChainRegistry(tmp_path / "chain.sqlite3")
    model = ModelManifest(model_id="ailovanta-owned", version="candidate", manifest_hash="sha256:runtime-manifest")
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
    binding = bindings.register_binding(
        runtime_model=runtime.get_model(model.key),
        artifact={
            "artifact_id": "artifact-model-record",
            "artifact_hash": "sha256:model-artifact-record",
            "checkpoint_uri": "file://" + str(checkpoint),
        },
        backend_ref="file://" + str(checkpoint),
        status="active",
    )
    routes.set_active("owned-chat/default", model.key, binding_id=binding["binding_id"])
    checker = RouteHealth(routes=routes, bindings=bindings, doctor=OwnedDoctor(bindings=bindings, runtime=runtime), chain=chain)
    return checker, binding, chain


def test_route_health_chain_gate_blocks_unanchored_event(tmp_path: Path) -> None:
    checker, binding, chain = _ready_checker(tmp_path)
    chain.append_model_event(
        {
            "event_type": "model_artifact_promoted",
            "model_id": binding["model_id"],
            "version": binding["version"],
            "artifact_hash": binding["artifact_hash"],
            "runtime_manifest_hash": binding["runtime_manifest_hash"],
            "metadata": {"binding_id": binding["binding_id"]},
        }
    )

    result = checker.check("owned-chat/default", verify_chain=True)

    assert result["ok"] is False
    assert "chain_anchor:event_not_anchored" in result["blockers"]
    assert "chain_anchor:missing_anchor_receipt" in result["blockers"]


def test_route_health_chain_gate_passes_anchored_event(tmp_path: Path) -> None:
    checker, binding, chain = _ready_checker(tmp_path)
    event = chain.append_model_event(
        {
            "event_type": "model_artifact_promoted",
            "model_id": binding["model_id"],
            "version": binding["version"],
            "artifact_hash": binding["artifact_hash"],
            "runtime_manifest_hash": binding["runtime_manifest_hash"],
            "metadata": {"binding_id": binding["binding_id"]},
        }
    )
    chain.mark_anchored(
        event["event_id"],
        chain_tx="file://anchor.json",
        anchor_receipt={
            "anchor_id": "anchor_1",
            "anchor_uri": "file://anchor.json",
            "anchor_type": "file",
            "payload_hash": binding["artifact_hash"],
            "payload": {"event_id": event["event_id"], "event_hash": event["event_hash"]},
        },
    )

    result = checker.check("owned-chat/default", verify_chain=True)

    assert result["ok"] is True
    assert result["chain_anchor"]["ok"] is True
