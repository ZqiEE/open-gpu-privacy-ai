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
    assert "不是已训练完成" in result["answer"]
    assert "Token count" not in result["answer"]


def test_bound_runtime_answers_training_boundary_directly(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.bin"
    checkpoint.write_bytes(json.dumps({"backend": "jsonl-stat"}).encode("utf-8"))
    store = ArtifactBindingStore(tmp_path / "bindings.sqlite3")
    store.register_binding(
        {"model_id": "ailovanta-owned", "version": "candidate", "model_key": "ailovanta-owned:candidate", "manifest_hash": "sha256:runtime", "status": "active"},
        {"artifact_id": "artifact_1", "artifact_hash": "sha256:artifact", "checkpoint_uri": "file://" + str(checkpoint)},
        backend_kind="checkpoint-artifact",
        backend_ref="file://" + str(checkpoint),
        status="active",
    )

    trained = ArtifactBoundRuntime(store).chat("是自己训练的吗", "ailovanta-owned", "candidate")["answer"]
    identity = ArtifactBoundRuntime(store).chat("你是什么大模型", "ailovanta-owned", "candidate")["answer"]
    followup = ArtifactBoundRuntime(store).chat("我问你呢", "ailovanta-owned", "candidate")["answer"]

    assert "没有" in trained
    assert "不是自训练完成的大模型权重" in trained
    assert "artifact" in identity
    assert "没有已激活的自训练生成模型" in followup


def test_bound_runtime_lightweight_ngram_does_not_claim_trained_model(tmp_path: Path) -> None:
    model = tmp_path / "ngram_model.json"
    model.write_text(
        json.dumps(
            {
                "schema": "ailovanta.lightweight_ngram.v1",
                "rows": 6,
                "transitions": 4336,
                "train_loss": 2.143432,
                "counts": {},
            }
        ),
        encoding="utf-8",
    )
    store = ArtifactBindingStore(tmp_path / "bindings.sqlite3")
    store.register_binding(
        {"model_id": "ailovanta-owned", "version": "candidate", "model_key": "ailovanta-owned:candidate", "manifest_hash": "sha256:runtime", "status": "active"},
        {"artifact_id": "artifact_1", "artifact_hash": "sha256:artifact", "checkpoint_uri": "file://" + str(model)},
        backend_kind="lightweight-ngram",
        backend_ref="file://" + str(model),
        status="active",
    )

    code = ArtifactBoundRuntime(store).chat("你会写代码吗", "ailovanta-owned", "candidate")
    trained = ArtifactBoundRuntime(store).chat("你训练了吗", "ailovanta-owned", "candidate")
    persona = ArtifactBoundRuntime(store).chat("你是女的吗", "ailovanta-owned", "candidate")

    assert code["source"] == "artifact-bound-lightweight-ngram"
    assert "不会" in code["answer"]
    assert "不是能写代码的自训练大模型" in code["answer"]
    assert "没有训练出可对话/可写代码的大模型" in trained["answer"]
    assert "没有真实性别" in persona["answer"]


def test_bound_runtime_missing_binding() -> None:
    try:
        ArtifactBoundRuntime(ArtifactBindingStore(":memory:")).chat("hello", "x", "y")
    except BoundRuntimeUnavailable as exc:
        assert "no active artifact binding" in str(exc)
    else:
        raise AssertionError("expected unavailable")


def test_bound_runtime_does_not_use_candidate_binding(tmp_path: Path) -> None:
    model = tmp_path / "ngram_model.json"
    model.write_text(json.dumps({"schema": "ailovanta.lightweight_ngram.v1", "rows": 1, "transitions": 1, "train_loss": 1.0, "counts": {}}), encoding="utf-8")
    store = ArtifactBindingStore(tmp_path / "bindings.sqlite3")
    store.register_binding(
        {"model_id": "ailovanta-owned", "version": "candidate", "model_key": "ailovanta-owned:candidate", "manifest_hash": "sha256:runtime", "status": "candidate"},
        {"artifact_id": "artifact_1", "artifact_hash": "sha256:artifact", "checkpoint_uri": "file://" + str(model)},
        backend_kind="lightweight-ngram",
        backend_ref="file://" + str(model),
        status="candidate",
    )

    try:
        ArtifactBoundRuntime(store).chat("hello", "ailovanta-owned", "candidate")
    except BoundRuntimeUnavailable as exc:
        assert "no active artifact binding" in str(exc)
    else:
        raise AssertionError("candidate binding must not serve runtime chat")
