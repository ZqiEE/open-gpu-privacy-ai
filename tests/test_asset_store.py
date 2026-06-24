from pathlib import Path

from api.asset_store import ModelAssetStore


def test_put_and_get_asset(tmp_path: Path) -> None:
    store = ModelAssetStore(str(tmp_path))
    item = store.put(
        {
            "artifact_hash": "sha256:test123",
            "model_version": "v1",
            "storage_uri": "file://models/v1",
        }
    )

    assert item["digest"] == "sha256:test123"
    assert item["payload"]["model_version"] == "v1"
    assert store.get("sha256:test123") is not None
