from api.artifact_binding import ArtifactBindingStore
from api.owned_model_runtime import OwnedModelRequest, OwnedModelRuntime, OwnedModelUnavailable
from api.route_book import RouteBook


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
    routes = RouteBook(tmp_path / "routes.sqlite3")
    routes.set_active("owned-chat/default", "ailovanta-owned:candidate", binding_id=store.latest_for_model_statuses("ailovanta-owned:candidate", ("active",))["binding_id"])
    runtime = OwnedModelRuntime(DummyRegistry(), binding_store=store, route_book=routes)
    try:
        runtime.generate(OwnedModelRequest(prompt="hello"))
    except OwnedModelUnavailable as exc:
        assert "not locally reachable" in str(exc)
    else:
        raise AssertionError("expected unavailable")


def test_owned_runtime_requires_active_route_for_binding(tmp_path) -> None:
    store = ArtifactBindingStore(tmp_path / "bindings.sqlite3")
    model_path = tmp_path / "model.json"
    model_path.write_text("{}", encoding="utf-8")
    store.register_binding(
        {"model_id": "ailovanta-owned", "version": "candidate", "model_key": "ailovanta-owned:candidate", "manifest_hash": "sha256:r", "status": "active"},
        {"artifact_id": "artifact_1", "artifact_hash": "sha256:a", "checkpoint_uri": model_path.resolve().as_uri()},
        backend_kind="checkpoint-artifact",
        backend_ref=model_path.resolve().as_uri(),
        status="active",
    )
    runtime = OwnedModelRuntime(DummyRegistry(), binding_store=store, route_book=RouteBook(tmp_path / "routes.sqlite3"))

    try:
        runtime.generate(OwnedModelRequest(prompt="hello"))
    except OwnedModelUnavailable as exc:
        assert "owned route is not active" in str(exc)
    else:
        raise AssertionError("expected unavailable")


def test_owned_runtime_rejects_route_binding_mismatch(tmp_path) -> None:
    store = ArtifactBindingStore(tmp_path / "bindings.sqlite3")
    routes = RouteBook(tmp_path / "routes.sqlite3")
    model_path = tmp_path / "model.json"
    model_path.write_text("{}", encoding="utf-8")
    store.register_binding(
        {"model_id": "ailovanta-owned", "version": "candidate", "model_key": "ailovanta-owned:candidate", "manifest_hash": "sha256:r", "status": "active"},
        {"artifact_id": "artifact_1", "artifact_hash": "sha256:a", "checkpoint_uri": model_path.resolve().as_uri()},
        backend_kind="checkpoint-artifact",
        backend_ref=model_path.resolve().as_uri(),
        status="active",
    )
    routes.set_active("owned-chat/default", "ailovanta-owned:candidate", binding_id="different-binding")
    runtime = OwnedModelRuntime(DummyRegistry(), binding_store=store, route_book=routes)

    try:
        runtime.generate(OwnedModelRequest(prompt="hello"))
    except OwnedModelUnavailable as exc:
        assert "binding_id does not match" in str(exc)
    else:
        raise AssertionError("expected unavailable")
