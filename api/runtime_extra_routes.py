from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.catalog import Catalog
from api.local_runtime import LocalRuntime


router = APIRouter()
catalog = Catalog()
local_runtime = LocalRuntime()


class LoadIn(BaseModel):
    item_id: str


class GenerateIn(BaseModel):
    model_key: str
    prompt: str
    max_new_tokens: int = Field(default=128, ge=1, le=2048)


@router.post("/runtime/local/load")
def load_local(body: LoadIn) -> dict:
    item = catalog.get(body.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    model_key = f"{item['name']}:{item['version']}"
    return {"item": item, "runtime": local_runtime.load(model_key, item["location"])}


@router.get("/runtime/local/models")
def list_local() -> dict:
    return {"models": local_runtime.list()}


@router.post("/runtime/local/generate")
def generate_local(body: GenerateIn) -> dict:
    return local_runtime.generate(body.model_key, body.prompt, body.max_new_tokens)
