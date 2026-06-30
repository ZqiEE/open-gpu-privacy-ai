from api.parcel_receipts import normalize_receipt, export_receipts
from api.parcel_store import ParcelStore


def test_normalize_receipt_from_metrics() -> None:
    receipt = normalize_receipt(
        {
            "id": "out_1",
            "task_id": "task_1",
            "node_id": "node_1",
            "checkpoint_hash": "sha256:abc",
            "metrics": {"token_count": 12, "train_loss": 0.2, "eval_loss": 0.3},
        }
    )
    assert receipt["schema_version"] == "ailovanta.checkpoint_receipt.v1"
    assert receipt["task_id"] == "task_1"
    assert receipt["token_count"] == 12
    assert receipt["receipt_hash"].startswith("sha256:")


def test_export_receipts_from_outbox(tmp_path) -> None:
    store = ParcelStore(tmp_path / "parcels")
    store.put_outbox({"id": "out_1", "task_id": "task_1", "node_id": "node_1", "checkpoint_hash": "sha256:abc"})
    result = export_receipts(store=store, output_path=tmp_path / "receipts.json", require_proof=False)
    assert result["ok"] is True
    assert result["count"] == 1
    assert (tmp_path / "receipts.json").exists()


def test_export_receipts_respects_required_proof(tmp_path) -> None:
    store = ParcelStore(tmp_path / "parcels")
    store.put_outbox({"id": "out_1", "task_id": "task_1", "node_id": "node_1", "checkpoint_hash": "sha256:abc"})
    result = export_receipts(store=store, output_path=tmp_path / "receipts.json", require_proof=True)
    assert result["ok"] is True
    assert result["count"] == 0
    assert result["rejected_count"] == 1
