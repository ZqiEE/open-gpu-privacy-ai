from api.node_proof import attach_proof
from api.parcel_receipts import export_receipts
from api.parcel_store import ParcelStore


def test_pg(tmp_path, monkeypatch) -> None:
    store = ParcelStore(tmp_path / "p")
    store.put_outbox(attach_proof({"id": "a", "task_id": "t", "node_id": "n", "checkpoint_hash": "sha256:a"}, "n", "s"))
    store.put_outbox({"id": "b", "task_id": "t2", "node_id": "m", "checkpoint_hash": "sha256:b"})
    monkeypatch.setenv("AILOVANTA_NODE_SECRETS_JSON", '{"n":"s"}')
    data = export_receipts(store=store, output_path=tmp_path / "o.json", require_proof=True)
    assert data["count"] == 1
    assert data["rejected_count"] == 1
