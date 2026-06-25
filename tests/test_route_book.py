from api.route_book import RouteBook


def test_route_book_set_disable(tmp_path) -> None:
    store = RouteBook(tmp_path / "routes.sqlite3")
    route = store.set_active("owned-chat/default", "ailovanta-owned:candidate", binding_id="b1")
    assert route["status"] == "active"
    assert store.active("owned-chat/default")["model_key"] == "ailovanta-owned:candidate"
    disabled = store.disable("owned-chat/default", reason="test")
    assert disabled["status"] == "disabled"
    assert store.active("owned-chat/default") is None
