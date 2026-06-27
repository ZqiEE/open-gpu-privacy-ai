from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.catalog import Catalog
from api.runtime_router import ModelManifest
from api.runtime_store import RuntimeStore


router = APIRouter()
catalog = Catalog()
runtime = RuntimeStore()


class ItemIn(BaseModel):
    name: str
    version: str
    location: str
    source_job_id: str = "manual"
    kind: str = "adapter"
    digest: str | None = None
    metrics: dict = Field(default_factory=dict)
    status: str = "candidate"
    notes: str = ""


class PublishIn(BaseModel):
    privacy_level: str = "public"
    min_gpu_memory_gb: float = 0.0
    allowed_pools: list[str] = Field(default_factory=lambda: ["small_gpu_pool", "large_gpu_pool", "enterprise_pool"])
    quantization: str = "unknown"
    context_length: int = 4096
    adapter_compatible: bool = True


@router.post("/catalog/items")
def add_item(body: ItemIn) -> dict:
    return {"item": catalog.add(body.model_dump())}


@router.get("/catalog/items")
def list_items(status: str | None = None) -> dict:
    return {"items": catalog.list(status=status)}


@router.post("/catalog/items/{item_id}/validate")
def validate_item(item_id: str) -> dict:
    item = catalog.set_status(item_id, "validated")
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    return {"item": item}


@router.post("/catalog/items/{item_id}/publish")
def publish_item(item_id: str, body: PublishIn | None = None) -> dict:
    item = catalog.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    if item.get("status") not in {"validated", "published"}:
        raise HTTPException(status_code=400, detail="item must be validated before publish")
    opts = body or PublishIn()
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
    manifest = catalog.write_manifest(item, {"status": "active", "model_key": f"{item['name']}:{item['version']}", "runtime_model": runtime_model})
    return {"item": item, "runtime_model": runtime_model, "manifest": manifest}
