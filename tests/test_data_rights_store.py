from pathlib import Path

from api.data_rights_store import DataRightsStore


def test_register_source_record(tmp_path: Path) -> None:
    store = DataRightsStore(tmp_path / "data_rights.sqlite3")
    source = store.register(
        {
            "source_id": "src_demo",
            "source_uri": "dataset://demo",
            "source_type": "uploaded",
            "authorized_by": "owner",
            "authorization_basis": "demo",
            "allowed_uses": ["rag", "eval"],
        }
    )
    assert source["source_id"] == "src_demo"
    assert source["allowed_uses"] == ["eval", "rag"]
