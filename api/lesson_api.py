from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from api.distill_data import build_distill_records, write_distill_jsonl

router = APIRouter(prefix="/lessons", tags=["lessons"])


class BuildBody(BaseModel):
    input: str = "runtime_data/teacher_code_samples.jsonl"
    output: str = "runtime_data/distill_corpus.jsonl"
    min_score: float = 0.0


@router.post("/build")
def build(body: BuildBody) -> dict:
    records = build_distill_records(body.input, min_score=body.min_score)
    result = write_distill_jsonl(records, body.output)
    return {"ok": bool(records), "result": result}
