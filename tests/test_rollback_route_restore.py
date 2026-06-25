import json
from time import time

from api.artifact_binding import ArtifactBindingStore
from api.model_monitor import ModelMonitorStore
from api.rollback_executor import RollbackExecutor
from api.route_book import RouteBook
from api.runtime_store import RuntimeStore


def test_rollback_restores_previous_route(tmp_path) -> None:
    routes = RouteBook(tmp_path / "routes.sqlite3")
    routes.set_active("owned-chat/default", "bad:model")
    monitor = ModelMonitorStore(tmp_path / "monitor")
    live = {"live_id": "live_1", "model": "bad:model", "previous_model": "stable:model", "status": "live", "created_at": time()}
    (monitor.live_dir / "live_1.json").write_text(json.dumps(live), encoding="utf-8")
    executor = RollbackExecutor(
        monitor=monitor,
        runtime=RuntimeStore(tmp_path / "runtime.sqlite3"),
        binding_store=ArtifactBindingStore(tmp_path / "bindings.sqlite3"),
        route_book=routes,
        log_root=tmp_path / "logs",
    )
    result = executor.execute_action({"action": "rollback", "model": "bad:model", "action_id": "a1"})
    assert result["executed"] is True
    assert routes.active("owned-chat/default")["model_key"] == "stable:model"
