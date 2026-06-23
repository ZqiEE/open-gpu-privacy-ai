from __future__ import annotations

import json

from api.distributed_model_registry import DistributedModelRegistry
from api.gateway_payload import build_gateway_payload
from api.inference_gateway import InferenceGateway
from api.model_node_inventory import ModelNodeInventory
from api.model_package import build_model_package
from api.object_store_adapter import LocalObjectStoreAdapter


def seed_model() -> None:
    store = LocalObjectStoreAdapter()
    registry = DistributedModelRegistry()
    inventory = ModelNodeInventory()
    saved_object = store.put_json({"adapter": "gateway-demo", "format": "demo"}, prefix="adapter")
    package = build_model_package(
        name="gateway-private-model",
        version="v0.1",
        base="open-base-demo",
        adapter_hash=saved_object["hash"],
        data_hash="authorized_demo_data",
        score=0.91,
        object_ref=saved_object["object_id"],
        tags=["private", "gateway"],
    )
    saved = registry.register(package)
    inventory.upsert_node_package("node_gateway_gpu", saved["package_hash"], saved["runtime"], 24, True, 0.98)


def main() -> None:
    seed_model()
    payload = build_gateway_payload("Explain the decentralized AI network in one paragraph.", user_ref="demo-user", tag="gateway", min_score=0.5, require_gpu=True)
    result = InferenceGateway().handle(payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
