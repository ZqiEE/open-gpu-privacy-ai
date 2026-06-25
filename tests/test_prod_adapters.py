import json

from api.anchor_adapter import FileAnchorAdapter
from api.artifact_store import LocalArtifactStore
from api.prod_config import load_config
from api.prod_ready import check_production_ready


def test_local_artifact_store(tmp_path) -> None:
    source = tmp_path / "artifact.json"
    source.write_text(json.dumps({"ok": True}), encoding="utf-8")
    stored = LocalArtifactStore(tmp_path / "store").put_file(source, "a1")
    assert stored.artifact_hash.startswith("sha256:")
    assert stored.store == "local"


def test_file_anchor(tmp_path) -> None:
    record = FileAnchorAdapter(tmp_path / "anchors").anchor({"artifact_hash": "sha256:x"})
    assert record.payload_hash == "sha256:x"
    assert record.anchor_type == "file"


def test_prod_config_loads() -> None:
    assert load_config().artifact_store == "local"


def test_prod_ready_returns_blockers() -> None:
    result = check_production_ready(route_key="missing/route")
    assert result["ok"] is False
