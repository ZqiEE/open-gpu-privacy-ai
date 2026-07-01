from __future__ import annotations

from api.main_release_ready import app


def test_release_ready_mounts_foundation_bridge_routes() -> None:
    paths = {route.path for route in app.routes}
    required = {
        "/core/results",
        "/foundation/jobs",
        "/foundation/results/import",
        "/foundation/pipeline/run",
        "/learning/foundation/jobs",
        "/learning/foundation/run",
        "/learning/gate/run",
        "/artifact-bindings",
        "/model-monitor/shadow",
        "/model-monitor/live",
        "/ops/foundation-artifact/ready",
        "/ops/release/gate",
    }
    missing = sorted(required - paths)
    assert not missing, missing
