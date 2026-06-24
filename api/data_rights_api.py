from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.data_rights_store import DataRightsStore

router = APIRouter(prefix="/data", tags=["data-rights"])
data_rights = DataRightsStore()


class DataSourceRegister(BaseModel):
    source_id: str | None = None
    source_uri: str
    source_type: Literal["owner_authorized", "partner", "licensed", "uploaded", "public_domain", "open_dataset"] = "owner_authorized"
    authorized_by: str
    authorization_basis: str
    allowed_uses: list[Literal["index", "rag", "inference", "finetune", "pretrain", "eval"]]
    scope_note: str = ""
    proof_uri: str = ""
    status: Literal["active", "blocked", "expired"] = "active"


@router.post("/sources")
def register_data_source(body: DataSourceRegister) -> dict:
    try:
        source = data_rights.register(body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "source": source}


@router.get("/sources")
def list_data_sources(status: str | None = None, limit: int = 100) -> dict:
    return {"sources": data_rights.list_sources(status=status, limit=limit)}


@router.get("/sources/{source_id}")
def get_data_source(source_id: str) -> dict:
    source = data_rights.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="data source not found")
    return {"source": source}


@router.get("/sources/{source_id}/check")
def check_data_source_use(source_id: str, requested_use: str = "finetune") -> dict:
    return data_rights.check_use(source_id, requested_use)
