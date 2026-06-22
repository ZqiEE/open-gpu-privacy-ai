from __future__ import annotations

import tempfile
from pathlib import Path

from api.distributed_model_registry import DistributedModelRegistry
from api.model_node_inventory import ModelNodeInventory
from api.model_package import build_model_package
from api.model_router import ModelRouter


def test_model_router_finds_gpu_node_for_best_package() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "models.sqlite3"
        registry = DistributedModelRegistry(db)
        inventory = ModelNodeInventory(db)
        package = registry.register(build_model_package("demo", "v1", "base", "a", "d", 0.95, "obj", tags=["private"]))
        inventory.upsert_node_package("node_gpu", package["package_hash"], package["runtime"], 24, True, 0.99)
        route = ModelRouter(registry, inventory).route(tag="private", min_score=0.5, require_gpu=True)
        assert route["routable"] is True
        assert route["node"]["node_id"] == "node_gpu"
