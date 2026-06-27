from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.catalog import Catalog
from api.wio import verify_result


router = APIRouter()
catalog = Catalog()


class ReceiptCatalogIn(BaseModel):
    receipt: dict
    name: str
    version: str
    kind: str = "adapter"
    metrics: dict = Field(default_factory=dict)
    require_valid: bool = True


@router.post("/catalog/from-receipt")
def catalog_from_receipt(body: ReceiptCatalogIn) -> dict:
    checked = verify_result(body.receipt)
    if body.require_valid and not checked.get("ok"):
        raise HTTPException(status_code=400, detail=checked)
    item = catalog.add({
        "name": body.name,
        "version": body.version,
        "source_job_id": body.receipt.get("task_id", "receipt"),
        "location": body.receipt["checkpoint_uri"],
        "artifact_uri": body.receipt["checkpoint_uri"],
        "artifact_hash": body.receipt["checkpoint_hash"],
        "kind": body.kind,
        "digest": body.receipt["checkpoint_hash"],
        "metrics": body.metrics,
        "proof": checked,
        "status": "candidate",
        "notes": "created from verified receipt",
    })
    return {"checked": checked, "item": item}
