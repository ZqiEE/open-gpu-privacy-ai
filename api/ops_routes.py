from __future__ import annotations

from fastapi import APIRouter, Depends

from api.admin_security import admin_token_header
from api.migrations import MigrationRunner


router = APIRouter(dependencies=[Depends(admin_token_header)])
runner = MigrationRunner()


@router.get("/ops/migrations")
def migration_status() -> dict:
    return runner.status()


@router.post("/ops/migrations/run")
def run_migrations() -> dict:
    return runner.run()
