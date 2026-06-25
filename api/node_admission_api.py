from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from api.node_admission import admit_runtime_node, choose_allowed_pool, rules_summary

router = APIRouter(prefix="/node-admission", tags=["node-admission"])


class AdmissionBody(BaseModel):
    node: dict[str, Any]


class PoolBody(BaseModel):
    node: dict[str, Any]
    trust_score: float | None = None


@router.get("/rules")
def get_rules() -> dict[str, Any]:
    return {"rules": rules_summary()}


@router.post("/check")
def check_node(body: AdmissionBody) -> dict[str, Any]:
    return admit_runtime_node(body.node)


@router.post("/choose-pool")
def choose_pool(body: PoolBody) -> dict[str, Any]:
    return choose_allowed_pool(body.node, body.trust_score)
