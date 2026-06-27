from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.catalog import Catalog
from api.humaneval_lite import run_humaneval_lite


router = APIRouter()
catalog = Catalog()


class EvalIn(BaseModel):
    candidate_dir: str
    task_path: str
    timeout: int = Field(default=5, ge=1, le=60)


class CatalogEvalIn(BaseModel):
    task_path: str
    timeout: int = Field(default=5, ge=1, le=60)


@router.post("/benchmarks/humaneval-lite")
def humaneval_lite(body: EvalIn) -> dict:
    return run_humaneval_lite(body.candidate_dir, body.task_path, body.timeout)


@router.post("/benchmarks/catalog/{item_id}/humaneval-lite")
def humaneval_lite_catalog(item_id: str, body: CatalogEvalIn) -> dict:
    item = catalog.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    result = run_humaneval_lite(item["location"], body.task_path, body.timeout)
    report_path = Path(item["location"]) / "humaneval_lite_report.json"
    report_path.write_text(__import__("json").dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if result["passed"]:
        item = catalog.set_status(item_id, "validated") or item
    return {"item": item, "benchmark": result, "report_path": str(report_path)}
