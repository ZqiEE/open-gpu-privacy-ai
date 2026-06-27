from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from api.local_runtime import LocalRuntime


app = FastAPI(title="Ailovanta Runtime Node", version="0.1.0")
runtime = LocalRuntime()


class LoadRequest(BaseModel):
    model_key: str
    location: str


class GenerateRequest(BaseModel):
    model_key: str
    prompt: str
    max_new_tokens: int = Field(default=128, ge=1, le=2048)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "loaded": runtime.list()}


@app.post("/load")
def load_model(body: LoadRequest) -> dict:
    return runtime.load(body.model_key, body.location)


@app.get("/models")
def list_models() -> dict:
    return {"models": runtime.list()}


@app.post("/generate")
def generate(body: GenerateRequest) -> dict:
    return runtime.generate(body.model_key, body.prompt, body.max_new_tokens)
