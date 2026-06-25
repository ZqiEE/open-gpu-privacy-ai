from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from api.parcel_receipts import export_receipts
from api.parcel_store import ParcelStore

router = APIRouter(prefix="/parcel-export", tags=["parcel-export"])
store = ParcelStore()


class ExportBody(BaseModel):
    output_path: str = "runtime_data/parcels/checkpoint_receipts.json"
    require_proof: bool | None = None


@router.post("/receipts")
def receipts(body: ExportBody) -> dict[str, Any]:
    return export_receipts(store=store, output_path=body.output_path, require_proof=body.require_proof)
