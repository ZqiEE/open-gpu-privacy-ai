from __future__ import annotations

from fastapi import APIRouter

from api.migrations import MigrationRunner


router = APIRouter()
runner = MigrationRunner()


@router.get("/ops/migrations")
def migration_status() -> dict:
    return runner.status()


@router.post("/ops/migrations/run")
def run_migrations() -> dict:
    return runner.run()
