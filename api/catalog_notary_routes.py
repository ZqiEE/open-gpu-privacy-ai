from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.anchor_adapter import get_anchor_adapter
from api.catalog import Catalog


router = APIRouter()
catalog = Catalog()


@router.post("/catalog/items/{item_id}/notarize")
def notarize_catalog_item(item_id: str) -> dict:
    item = catalog.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    payload = {
        "catalog_id": item["id"],
        "name": item["name"],
        "version": item["version"],
        "artifact_uri": item.get("artifact_uri") or item.get("location"),
        "artifact_hash": item.get("artifact_hash") or item.get("digest"),
        "receipt": item.get("proof"),
    }
    if not payload["artifact_hash"]:
        raise HTTPException(status_code=400, detail="artifact hash required")
    if not payload["receipt"]:
        raise HTTPException(status_code=400, detail="worker receipt required")
    anchor_receipt = get_anchor_adapter().anchor(payload).to_dict()
    item = catalog.patch(item_id, {"anchor_receipt": anchor_receipt}) or item
    return {"item": item, "anchor_receipt": anchor_receipt}
