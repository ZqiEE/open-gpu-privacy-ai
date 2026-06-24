from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.chain_registry import ChainRegistry

router = APIRouter(prefix="/chain", tags=["chain-registry"])
chain_registry = ChainRegistry()


class ChainModelEventRequest(BaseModel):
    event_type: Literal["model_artifact_promoted", "runtime_manifest_registered", "worker_attested"] = "model_artifact_promoted"
    model_id: str
    version: str
    artifact_hash: str
    runtime_manifest_hash: str
    metadata: dict[str, Any] = {}
    anchor_status: str = "local_pending"
    chain_tx: str = ""


@router.post("/events")
def append_chain_event(body: ChainModelEventRequest) -> dict:
    try:
        event = chain_registry.append_model_event(body.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=400, detail="missing field: " + str(exc)) from exc
    return {"ok": True, "event": event}


@router.get("/events")
def list_chain_events(limit: int = 100) -> dict:
    return {"events": chain_registry.list_events(limit=limit)}
