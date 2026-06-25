from api.node_trust import NodeTrustStore


def test_node_trust_register_and_disable(tmp_path) -> None:
    store = NodeTrustStore(tmp_path / "trust.sqlite3")
    item = store.register("n1", "secret", trust_score=0.9)
    assert item["node_id"] == "n1"
    assert item["secret_hash"].startswith("sha256:")
    assert store.verify_secret("n1", "secret")["ok"] is True
    store.set_status("n1", "disabled")
    assert store.verify_secret("n1", "secret")["ok"] is False
