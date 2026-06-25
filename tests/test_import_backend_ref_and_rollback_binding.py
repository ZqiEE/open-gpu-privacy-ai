from api.artifact_binding import ArtifactBindingStore
from api.chain_registry import ChainRegistry
from api.core_result_store import CoreResultStore
from api.model_monitor import ModelMonitorStore
from api.rollback_executor import RollbackExecutor
from api.runtime_store import RuntimeStore


def foundation_payload() -> dict:
    return {
        "plan": {"model": {"model_id": "ailovanta-owned"}},
        "artifact": {
            "artifact_id": "artifact_1",
            "artifact_hash": "sha256:artifact",
            "model_id": "ailovanta-owned",
            "version": "candidate",
            "source_plan_id": "plan_1",
            "checkpoint_uri": "artifact://plan/merged",
            "backend_kind": "checkpoint-artifact",
            "backend_ref": "file:///tmp/checkpoint.bin",
        },
    }


def test_import_prefers_backend_ref(tmp_path) -> None:
    from api.foundation_result_import import import_foundation_result

    result = import_foundation_result(
        foundation_payload(),
        core_results=CoreResultStore(tmp_path / "core.sqlite3"),
        runtime_store=RuntimeStore(tmp_path / "runtime.sqlite3"),
        chain_registry=ChainRegistry(tmp_path / "chain"),
        binding_store=ArtifactBindingStore(tmp_path / "bindings.sqlite3"),
    )
    assert result["artifact_binding"]["backend_ref"] == "file:///tmp/checkpoint.bin"
    assert result["chain_event"]["metadata"]["backend_ref"] == "file:///tmp/checkpoint.bin"


def test_rollback_marks_binding_rolled_back(tmp_path) -> None:
    from api.runtime_router import ModelManifest

    runtime = RuntimeStore(tmp_path / "runtime.sqlite3")
    bindings = ArtifactBindingStore(tmp_path / "bindings.sqlite3")
    monitor = ModelMonitorStore(tmp_path / "monitor")
    runtime.register_model(
        ModelManifest(
            model_id="ailovanta-owned",
            version="candidate",
            manifest_hash="sha256:r",
            privacy_level="protected",
            min_gpu_memory_gb=0,
            allowed_pools=["trusted_runtime_pool"],
            quantization="candidate",
            context_length=8192,
            adapter_compatible=True,
            status="active",
        )
    )
    bindings.register_binding(
        {"model_id": "ailovanta-owned", "version": "candidate", "model_key": "ailovanta-owned:candidate", "manifest_hash": "sha256:r", "status": "active"},
        {"artifact_id": "artifact_1", "artifact_hash": "sha256:a", "checkpoint_uri": "file:///tmp/checkpoint.bin"},
        status="active",
    )
    shadow = monitor.register_shadow("ailovanta-owned:candidate", "ailovanta-owned:baseline")
    monitor.promote_live(shadow["shadow_id"])
    action = monitor._write_action({"action": "rollback", "model": "ailovanta-owned:candidate", "reason": "test"})
    result = RollbackExecutor(monitor=monitor, runtime=runtime, binding_store=bindings, log_root=tmp_path / "logs").execute_action(action)
    assert result["bad_binding_update"]["after"] == "rolled_back"
    assert bindings.latest_for_model("ailovanta-owned:candidate")["status"] == "rolled_back"
