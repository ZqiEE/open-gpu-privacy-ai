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
