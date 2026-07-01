from api.artifact_binding import ArtifactBindingStore
from api.chain_registry import ChainRegistry
from api.core_result_store import CoreResultStore
from api.foundation_result_import import import_foundation_result
from api.runtime_store import RuntimeStore

GOOD_HASH = "sha256:" + "a" * 64


def test_import_foundation_result_registers_runtime_and_chain(tmp_path) -> None:
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text("{}", encoding="utf-8")
    checkpoint_uri = "file://" + str(checkpoint.resolve())
    result = import_foundation_result(
        {
            "plan": {
                "plan_id": "foundation_plan_1",
                "plan_hash": "sha256:" + "b" * 64,
                "model": {"model_id": "ailovanta-owned", "target_version": "candidate"},
            },
            "artifact": {
                "schema_version": "ailovanta.foundation_artifact.v1",
                "artifact_id": "foundation_artifact_1",
                "model_id": "ailovanta-owned",
                "version": "candidate",
                "source_plan_id": "foundation_plan_1",
                "checkpoint_uri": checkpoint_uri,
                "backend_ref": checkpoint_uri,
                "artifact_hash": GOOD_HASH,
                "promotion_status": "candidate",
            },
        },
        core_results=CoreResultStore(tmp_path / "core.sqlite3"),
        runtime_store=RuntimeStore(tmp_path / "runtime.sqlite3"),
        chain_registry=ChainRegistry(tmp_path / "chain.sqlite3"),
        binding_store=ArtifactBindingStore(tmp_path / "bindings.sqlite3"),
    )

    assert result["runtime_model"]["model_id"] == "ailovanta-owned"
    assert result["runtime_model"]["manifest_hash"] == GOOD_HASH
    assert result["chain_event"]["artifact_hash"] == GOOD_HASH
    assert result["runtime_ref_check"]["ready"] is True
