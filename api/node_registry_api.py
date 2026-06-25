from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.node_trust import NodeTrustStore

router = APIRouter(prefix="/node-registry", tags=["node-registry"])
store = NodeTrustStore()


class RegisterBody(BaseModel):
    node_id: str
    secret: str
    trust_score: float = 0.8
    metadata: dict[str, Any] = {}


class StatusBody(BaseModel):
    status: str


@router.post("/register")
def register(body: RegisterBody) -> dict[str, Any]:
    return {"ok": True, "node": store.register(body.node_id, body.secret, trust_score=body.trust_score, metadata=body.metadata)}


@router.get("")
def list_nodes(limit: int = 100) -> dict[str, Any]:
    return {"items": store.list_nodes(limit=limit)}


@router.get("/{node_id}")
def get_node(node_id: str) -> dict[str, Any]:
    item = store.get(node_id)
    if not item:
        raise HTTPException(status_code=404, detail="node not found")
    return {"node": item}


@router.post("/{node_id}/status")
def set_status(node_id: str, body: StatusBody) -> dict[str, Any]:
    item = store.set_status(node_id, body.status)
    if not item:
        raise HTTPException(status_code=404, detail="node not found")
    return {"node": item}
