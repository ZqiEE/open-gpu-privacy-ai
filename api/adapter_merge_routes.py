from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.adapter_merge import merge_adapters
from api.catalog import Catalog


router = APIRouter()
catalog = Catalog()


class AdapterMergeIn(BaseModel):
    item_ids: list[str]
    base_model: str
    name: str = "ailovanta-code"
    version: str = "merged-adapter-v0"
    output_dir: str | None = None


@router.post("/adapters/merge")
def merge_adapter_items(body: AdapterMergeIn) -> dict:
    items = []
    for item_id in body.item_ids:
        item = catalog.get(item_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"item not found: {item_id}")
        items.append(item)
    locations = [item["location"] for item in items]
    output_dir = body.output_dir or f"runtime_data/models/{body.name}-{body.version}"
    report = merge_adapters(body.base_model, locations, output_dir)
    new_item = catalog.add({"name": body.name, "version": body.version, "source_job_id": "adapter_merge", "location": report["location"], "kind": "merged_adapter", "metrics": {"score": 0.7, "merged_count": len(items)}, "status": "candidate", "notes": report["mode"]})
    return {"item": new_item, "merge": report}
