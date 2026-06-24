from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.asset_store import ModelAssetStore

router = APIRouter(prefix="/model-assets", tags=["model-assets"])
store = ModelAssetStore()


class AssetRecord(BaseModel):
    artifact_hash: str | None = None
    manifest_hash: str | None = None
    model_version: str | None = None
    storage_uri: str | None = None
    payload: dict[str, Any] = {}


@router.post("")
def put_asset(body: AssetRecord) -> dict:
    payload = body.model_dump()
    payload.update(payload.pop("payload") or {})
    try:
        item = store.put(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "asset": item}


@router.get("")
def list_assets(limit: int = 50) -> dict:
    return {"assets": store.list(limit=limit)}


@router.get("/{digest:path}")
def get_asset(digest: str) -> dict:
    item = store.get(digest)
    if not item:
        raise HTTPException(status_code=404, detail="asset not found")
    return {"asset": item}
