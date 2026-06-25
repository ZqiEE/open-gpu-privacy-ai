from api.artifact_binding import ArtifactBindingStore
from api.chain_registry import ChainRegistry
from api.core_result_store import CoreResultStore
from api.foundation_result_import import import_foundation_result
from api.runtime_ref import check_runtime_ref
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
    return {
        "core_results": CoreResultStore(tmp_path / "core.sqlite3"),
        "runtime_store": RuntimeStore(tmp_path / "runtime.sqlite3"),
        "chain_registry": ChainRegistry(tmp_path / "chain"),
        "binding_store": ArtifactBindingStore(tmp_path / "bindings.sqlite3"),
    }


def test_check_runtime_ref_ready_file(tmp_path) -> None:
    ckpt = tmp_path / "checkpoint.bin"
    ckpt.write_text('{"backend":"jsonl-stat","token_count":3}', encoding="utf-8")
    result = import_foundation_result(payload("file://" + str(ckpt)), **stores(tmp_path))
    assert result["runtime_ref_check"]["ready"] is True
    assert result["artifact_binding"]["status"] == "active"


def test_import_marks_missing_ref_unavailable(tmp_path) -> None:
    missing = tmp_path / "missing.bin"
    result = import_foundation_result(payload("file://" + str(missing)), **stores(tmp_path))
    assert result["runtime_ref_check"]["ready"] is False
    assert result["artifact_binding"]["status"] == "unavailable"
    assert result["chain_event"]["metadata"]["ref_ready"] is False


def test_check_runtime_ref_directory(tmp_path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    item = {"backend_ref": "file://" + str(model_dir), "backend_kind": "transformers-local", "binding_id": "b1"}
    assert check_runtime_ref(item)["ready"] is True
