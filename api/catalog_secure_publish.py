from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.catalog import Catalog
from api.receipt_gate import ready_for_catalog_publish
from api.runtime_router import ModelManifest
from api.runtime_store import RuntimeStore


router = APIRouter()
catalog = Catalog()
runtime = RuntimeStore()


class SecurePublishIn(BaseModel):
    privacy_level: str = "public"
    min_gpu_memory_gb: float = 0.0
    allowed_pools: list[str] = Field(default_factory=lambda: ["small_gpu_pool", "large_gpu_pool", "enterprise_pool"])
    quantization: str = "unknown"
    context_length: int = 4096
    adapter_compatible: bool = True


def manifest_ready(item: dict) -> dict:
    data = item.get("artifact_manifest")
    if not isinstance(data, dict):
        return {"ok": False, "reason": "artifact manifest required"}
    if int(data.get("chunk_count") or 0) <= 0:
        return {"ok": False, "reason": "artifact manifest chunks required"}
    if not data.get("manifest_hash"):
        return {"ok": False, "reason": "artifact manifest hash required"}
    return {"ok": True}


@router.post("/catalog/items/{item_id}/publish")
def secure_publish_item(item_id: str, body: SecurePublishIn | None = None) -> dict:
    item = catalog.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    if item.get("status") not in {"validated", "published"}:
        raise HTTPException(status_code=400, detail="item must be validated before publish")
    gate = ready_for_catalog_publish(item)
    if not gate.get("ok"):
        raise HTTPException(status_code=400, detail=gate)
    manifest_gate = manifest_ready(item)
    if not manifest_gate.get("ok"):
        raise HTTPException(status_code=400, detail=manifest_gate)
    opts = body or SecurePublishIn()
    runtime_model = runtime.register_model(
        ModelManifest(
            model_id=item["name"],
            version=item["version"],
            manifest_hash=item["digest"],
            privacy_level=opts.privacy_level,
            min_gpu_memory_gb=opts.min_gpu_memory_gb,
            allowed_pools=opts.allowed_pools,
            quantization=opts.quantization,
            context_length=opts.context_length,
            adapter_compatible=opts.adapter_compatible,
            status="active",
        )
    )
    item = catalog.set_status(item_id, "published") or item
    manifest = catalog.write_manifest(item, {"status": "active", "model_key": f"{item['name']}:{item['version']}", "runtime_model": runtime_model, "receipt": item.get("anchor_receipt")})
    return {"item": item, "runtime_model": runtime_model, "manifest": manifest}
