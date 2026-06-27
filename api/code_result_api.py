from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from api.code_result_import import CoreCodeResultImporter

router = APIRouter()
code_results = CoreCodeResultImporter()


class CoreCodeResultRequest(BaseModel):
    manifest: dict[str, Any]


@router.post("/code/core-results/apply")
def apply_core_code_result(body: CoreCodeResultRequest) -> dict:
    return code_results.import_result(body.manifest)


@router.get("/code/core-results")
def list_core_code_results() -> dict:
    return {"results": code_results.list_results()}
