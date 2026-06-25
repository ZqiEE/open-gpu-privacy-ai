import json
from pathlib import Path

from api.artifact_binding import ArtifactBindingStore
from api.bound_runtime import ArtifactBoundRuntime, BoundRuntimeUnavailable, resolve_local_ref


def test_resolve_file_ref(tmp_path: Path) -> None:
    path = tmp_path / "checkpoint.bin"
    assert resolve_local_ref("file://" + str(path)) == path


def test_bound_runtime_loads_checkpoint_metadata(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.bin"
    checkpoint.write_bytes(json.dumps({"backend": "jsonl-stat", "token_count": 12, "train_loss": 0.1, "eval_loss": 0.2}).encode("utf-8"))
    store = ArtifactBindingStore(tmp_path / "bindings.sqlite3")
    store.register_binding(
        {"model_id": "ailovanta-owned", "version": "candidate", "model_key": "ailovanta-owned:candidate", "manifest_hash": "sha256:runtime", "status": "active"},
        {"artifact_id": "artifact_1", "artifact_hash": "sha256:artifact", "checkpoint_uri": "file://" + str(checkpoint)},
        backend_kind="checkpoint-artifact",
        backend_ref="file://" + str(checkpoint),
        status="active",
    )
    result = ArtifactBoundRuntime(store).chat("hello", "ailovanta-owned", "candidate")
    assert result["source"] == "artifact-bound-checkpoint"
    assert "Token count" in result["answer"]


def test_bound_runtime_missing_binding() -> None:
    try:
        ArtifactBoundRuntime(ArtifactBindingStore(":memory:")).chat("hello", "x", "y")
    except BoundRuntimeUnavailable as exc:
        assert "no active artifact binding" in str(exc)
    else:
        raise AssertionError("expected unavailable")
