from api.artifact_binding import ArtifactBindingStore
from api.chain_registry import ChainRegistry
from api.model_warm import ModelWarm, WarmSpec
from api.runtime_store import RuntimeStore


def test_model_warm_rejects_missing_binding(tmp_path) -> None:
    result = ModelWarm(
        bindings=ArtifactBindingStore(tmp_path / "bindings.sqlite3"),
        runtime=RuntimeStore(tmp_path / "runtime.sqlite3"),
        chain=ChainRegistry(tmp_path / "chain"),
    ).run(WarmSpec())
    assert result["ok"] is False


def test_model_warm_registers_runtime_and_node(tmp_path) -> None:
    ckpt = tmp_path / "checkpoint.bin"
    ckpt.write_text('{"backend":"jsonl-stat"}', encoding="utf-8")
    bindings = ArtifactBindingStore(tmp_path / "bindings.sqlite3")
    runtime = RuntimeStore(tmp_path / "runtime.sqlite3")
    chain = ChainRegistry(tmp_path / "chain")
    bindings.register_binding(
        {"model_id": "ailovanta-owned", "version": "candidate", "model_key": "ailovanta-owned:candidate", "manifest_hash": "sha256:r", "status": "active"},
        {"artifact_id": "artifact_1", "artifact_hash": "sha256:a", "checkpoint_uri": "file://" + str(ckpt)},
        backend_kind="checkpoint-artifact",
        backend_ref="file://" + str(ckpt),
        status="active",
    )
    result = ModelWarm(bindings=bindings, runtime=runtime, chain=chain).run(WarmSpec())
    assert result["ok"] is True
    assert runtime.get_model("ailovanta-owned:candidate")["status"] == "active"
    assert "ailovanta-owned:candidate" in runtime.get_runtime("rt-owned-1")["cached_models"]
