from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.catalog import Catalog


router = APIRouter()
catalog = Catalog()


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
def publish_item(item_id: str) -> dict:
    item = catalog.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    if item.get("status") not in {"validated", "published"}:
        raise HTTPException(status_code=400, detail="item must be validated before publish")
    item = catalog.set_status(item_id, "published") or item
    manifest = catalog.write_manifest(item, {"status": "ready_for_runtime", "model_key": f"{item['name']}:{item['version']}"})
    return {"item": item, "manifest": manifest}
