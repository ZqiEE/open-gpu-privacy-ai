from __future__ import annotations

import json

from api.content_addressing import hash_object
from api.distributed_model_registry import DistributedModelRegistry
from api.model_node_inventory import ModelNodeInventory
from api.model_package import build_model_package
from api.model_router import ModelRouter
from api.object_store_adapter import LocalObjectStoreAdapter


def main() -> None:
    objects = LocalObjectStoreAdapter()
    registry = DistributedModelRegistry()
    inventory = ModelNodeInventory()

    adapter_payload = {"adapter": "demo-lora-adapter", "rank": 8, "format": "demo"}
    data_payload = {"dataset": "authorized-demo-corpus", "records": 3, "format": "demo"}
    adapter_object = objects.put_json(adapter_payload, prefix="adapter")
    data_object = objects.put_json(data_payload, prefix="data")

    package = build_model_package(
        name="demo-private-model",
        version="v0.2",
        base="open-base-demo",
        adapter_hash=adapter_object["hash"],
        data_hash=data_object["hash"],
        score=0.88,
        object_ref=adapter_object["object_id"],
        runtime="local-runtime",
        tags=["ai", "private", "rag"],
    )
    saved = registry.register(package)
    node = inventory.upsert_node_package("node_model_gpu", saved["package_hash"], saved["runtime"], memory_gb=24, has_gpu=True, health_score=0.96)
    route = ModelRouter(registry, inventory).route(tag="private", min_score=0.5, require_gpu=True)

    print(json.dumps({"adapter_object": adapter_object, "data_object": data_object, "package": saved, "node": node, "route": route, "registry": registry.summary(), "inventory": inventory.summary()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
