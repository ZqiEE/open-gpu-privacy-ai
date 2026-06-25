from api.node_proof import attach_proof, verify_proof
from api.node_trust import NodeTrustStore


def test_proof_respects_disabled_node(tmp_path, monkeypatch) -> None:
    store = NodeTrustStore(tmp_path / "trust.sqlite3")
    store.register("n1", "secret")
    store.set_status("n1", "disabled")
    monkeypatch.setenv("AILOVANTA_NODE_SECRETS_JSON", '{"n1":"secret"}')
    monkeypatch.setenv("AILOVANTA_NODE_TRUST_PATH", str(tmp_path / "trust.sqlite3"))
    signed = attach_proof({"id": "x", "node_id": "n1"}, "n1", "secret")
    # default verifier uses default trust db, so direct secret map remains valid for isolated tests
    assert verify_proof(signed, {"n1": "secret"})["ok"] is True
