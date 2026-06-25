from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from api.parcel_receipts import export_receipts
from api.parcel_store import ParcelStore

router = APIRouter(prefix="/parcels", tags=["parcels"])
store = ParcelStore()


class Batch(BaseModel):
    group_id: str
    items: list[dict[str, Any]]


class Item(BaseModel):
    payload: dict[str, Any]


class ExportRequest(BaseModel):
    output_path: str = "runtime_data/parcels/checkpoint_receipts.json"


@router.post("/push")
def push(body: Batch) -> dict:
    return {"ok": True, "result": store.put_many(body.group_id, body.items)}


@router.get("/pending")
def pending() -> dict:
    return {"items": store.list_inbox()}


@router.post("/submit")
def submit(body: Item) -> dict:
    return {"ok": True, "result": store.put_outbox(body.payload)}


@router.get("/submitted")
def submitted() -> dict:
    return {"items": store.list_outbox()}


@router.post("/receipts/export")
def export_checkpoint_receipts(body: ExportRequest) -> dict:
    return export_receipts(store=store, output_path=body.output_path)
