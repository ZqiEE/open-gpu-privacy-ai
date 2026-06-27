from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from api.qlora_smoke import run_qlora_smoke


router = APIRouter()


class QloraSmokeIn(BaseModel):
    base_model: str = "sshleifer/tiny-gpt2"


@router.post("/compat/qlora-smoke")
def qlora_smoke(body: QloraSmokeIn) -> dict:
    return run_qlora_smoke(body.base_model)
