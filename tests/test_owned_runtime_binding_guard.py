from api.artifact_binding import ArtifactBindingStore
from api.owned_model_runtime import OwnedModelRequest, OwnedModelRuntime, OwnedModelUnavailable


class DummyRegistry:
    def route(self, request):
        return {"assigned": True, "assignment": {"runtime_id": "rt", "node_id": "node", "model_manifest_hash": "sha256:r"}}


def test_owned_runtime_rejects_unreachable_binding(tmp_path) -> None:
    store = ArtifactBindingStore(tmp_path / "bindings.sqlite3")
    store.register_binding(
        {"model_id": "ailovanta-owned", "version": "candidate", "model_key": "ailovanta-owned:candidate", "manifest_hash": "sha256:r", "status": "active"},
        {"artifact_id": "artifact_1", "artifact_hash": "sha256:a", "checkpoint_uri": "file://" + str(tmp_path / "missing.bin")},
        backend_kind="checkpoint-artifact",
        backend_ref="file://" + str(tmp_path / "missing.bin"),
        status="active",
    )
    runtime = OwnedModelRuntime(DummyRegistry(), binding_store=store)
    try:
        runtime.generate(OwnedModelRequest(prompt="hello"))
    except OwnedModelUnavailable as exc:
        assert "not locally reachable" in str(exc)
    else:
        raise AssertionError("expected unavailable")
