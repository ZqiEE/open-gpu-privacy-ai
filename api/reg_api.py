from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from api.promote import gate, registry

router = APIRouter(prefix="/model-registry", tags=["model-registry"])


class PromoteBody(BaseModel):
    manifest: str | None = None
    eval_file: str = "runtime_data/code_eval.json"
    min_score: float = 1.0
    require_improvement: bool = True


@router.get("")
def list_registry() -> dict:
    return registry()


@router.post("/promote")
def promote(body: PromoteBody) -> dict:
    return gate(body.manifest, body.eval_file, body.min_score, body.require_improvement)
