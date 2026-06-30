from api.route_book import RouteBook
from api.route_health import RouteHealth


def test_route_health_missing_route(tmp_path) -> None:
    checker = RouteHealth(routes=RouteBook(tmp_path / "routes.sqlite3"))
    result = checker.check("owned-chat/default")
    assert result["ok"] is False
    assert "missing_route" in result["blockers"]


def test_route_health_disables_bad_route(tmp_path) -> None:
    routes = RouteBook(tmp_path / "routes.sqlite3")
    routes.set_active("owned-chat/default", "m:v")
    checker = RouteHealth(routes=routes)
    result = checker.disable_if_bad("owned-chat/default")
    assert result["changed"] is True
    assert routes.active("owned-chat/default") is None


def test_route_health_blocks_candidate_binding(tmp_path) -> None:
    from api.artifact_binding import ArtifactBindingStore
    from api.owned_doctor import OwnedDoctor
    from api.runtime_store import RuntimeStore

    checkpoint = tmp_path / "candidate.json"
    checkpoint.write_text("{}", encoding="utf-8")
    routes = RouteBook(tmp_path / "routes.sqlite3")
    bindings = ArtifactBindingStore(tmp_path / "bindings.sqlite3")
    runtime = RuntimeStore(tmp_path / "runtime.sqlite3")
    binding = bindings.register_binding(
        {"model_id": "ailovanta-owned", "version": "candidate", "model_key": "ailovanta-owned:candidate", "manifest_hash": "sha256:r", "status": "candidate"},
        {"artifact_id": "a", "artifact_hash": "sha256:a", "checkpoint_uri": checkpoint.resolve().as_uri()},
        backend_ref=checkpoint.resolve().as_uri(),
        status="candidate",
    )
    routes.set_active("owned-chat/default", "ailovanta-owned:candidate", binding_id=binding["binding_id"])

    result = RouteHealth(routes=routes, bindings=bindings, doctor=OwnedDoctor(bindings=bindings, runtime=runtime)).check("owned-chat/default")

    assert result["ok"] is False
    assert "binding_not_active" in result["blockers"]
