from api.node_proof import attach_proof, verify_proof
from api.node_trust import NodeTrustStore


def test_status_blocks_env_secret(tmp_path, monkeypatch) -> None:
    db = tmp_path / "trust.sqlite3"
    store = NodeTrustStore(db)
    store.register("n1", "secret")
    store.set_status("n1", "disabled")
    monkeypatch.setenv("AILOVANTA_NODE_TRUST_PATH", str(db))
    monkeypatch.setenv("AILOVANTA_NODE_SECRETS_JSON", '{"n1":"secret"}')
    signed = attach_proof({"id": "x", "node_id": "n1"}, "n1", "secret")
    assert verify_proof(signed)["reason"] == "node_not_active"
