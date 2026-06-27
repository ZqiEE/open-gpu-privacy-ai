from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.runtime_forwarder import RuntimeEndpointStore, post_json
from api.runtime_router import RuntimeRequest
from api.runtime_store import RuntimeStore


router = APIRouter()
endpoints = RuntimeEndpointStore()
runtime_store = RuntimeStore()


class EndpointIn(BaseModel):
    runtime_id: str
    url: str


class ForwardIn(BaseModel):
    request_id: str
    model_id: str
    version: str
    prompt: str
    max_new_tokens: int = Field(default=128, ge=1, le=2048)


@router.post("/runtime/endpoints")
def register_endpoint(body: EndpointIn) -> dict:
    return endpoints.register(body.runtime_id, body.url)


@router.get("/runtime/endpoints")
def list_endpoints() -> dict:
    return {"endpoints": endpoints.all()}


@router.post("/runtime/forward")
def forward_runtime(body: ForwardIn) -> dict:
    routed = runtime_store.route(RuntimeRequest(request_id=body.request_id, model_id=body.model_id, version=body.version))
    if not routed.get("assigned"):
        raise HTTPException(status_code=404, detail=routed)
    assignment = routed["assignment"]
    url = endpoints.get(assignment["runtime_id"])
    if not url:
        raise HTTPException(status_code=404, detail={"reason": "runtime endpoint not registered", "assignment": assignment})
    result = post_json(url + "/generate", {"model_key": f"{body.model_id}:{body.version}", "prompt": body.prompt, "max_new_tokens": body.max_new_tokens})
    return {"route": routed, "runtime_url": url, "result": result}
