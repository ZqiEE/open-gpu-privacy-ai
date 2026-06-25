from api.artifact_binding import ArtifactBindingStore
from api.chain_registry import ChainRegistry
from api.core_result_store import CoreResultStore
from api.foundation_result_import import import_foundation_result
from api.runtime_router import RuntimeRequest
from api.runtime_store import RuntimeStore


def payload(ref: str) -> dict:
    return {
        "plan": {"model": {"model_id": "ailovanta-owned"}},
        "artifact": {
            "artifact_id": "artifact_1",
            "artifact_hash": "sha256:artifact",
            "model_id": "ailovanta-owned",
            "version": "candidate",
            "source_plan_id": "plan_1",
            "checkpoint_uri": ref,
            "backend_kind": "checkpoint-artifact",
            "backend_ref": ref,
        },
    }


def stores(tmp_path):
    runtime = RuntimeStore(tmp_path / "runtime.sqlite3")
    return runtime, {
        "core_results": CoreResultStore(tmp_path / "core.sqlite3"),
        "runtime_store": runtime,
        "chain_registry": ChainRegistry(tmp_path / "chain"),
        "binding_store": ArtifactBindingStore(tmp_path / "bindings.sqlite3"),
    }


def test_missing_backend_ref_marks_runtime_unavailable(tmp_path) -> None:
    runtime, deps = stores(tmp_path)
    result = import_foundation_result(payload("file://" + str(tmp_path / "missing.bin")), **deps)
    assert result["artifact_binding"]["status"] == "unavailable"
    assert result["runtime_model"]["status"] == "unavailable"
    assert result["runtime_status_update"]["after"] == "unavailable"
    routed = runtime.route(RuntimeRequest(request_id="r1", model_id="ailovanta-owned", version="candidate"))
    assert routed["assigned"] is False
    assert routed["reason"] == "model manifest is not active"


def test_ready_backend_ref_keeps_runtime_active(tmp_path) -> None:
    runtime, deps = stores(tmp_path)
    ckpt = tmp_path / "checkpoint.bin"
    ckpt.write_text('{"backend":"jsonl-stat"}', encoding="utf-8")
    result = import_foundation_result(payload("file://" + str(ckpt)), **deps)
    assert result["artifact_binding"]["status"] == "active"
    assert result["runtime_model"]["status"] == "active"
    assert result["runtime_status_update"] is None
