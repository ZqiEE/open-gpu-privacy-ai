from __future__ import annotations

import tempfile
from pathlib import Path

from api.model_node_inventory import ModelNodeInventory


def test_model_node_inventory_tracks_nodes_for_package() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        inventory = ModelNodeInventory(Path(tmp) / "models.sqlite3")
        item = inventory.upsert_node_package("node_a", "hash_a", "runtime", 16, True, 0.9)
        assert item["node_id"] == "node_a"
        assert item["has_gpu"] is True
        assert inventory.nodes_for_package("hash_a")[0]["node_id"] == "node_a"
        assert inventory.summary()["entries"] == 1
