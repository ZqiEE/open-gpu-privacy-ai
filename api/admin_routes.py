from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


router = APIRouter()
BASE_DIR = Path(__file__).resolve().parents[1]


@router.get("/admin")
def admin_panel() -> FileResponse:
    path = BASE_DIR / "admin.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="admin.html not found")
    return FileResponse(path)


@router.get("/admin-secure")
def admin_secure_panel() -> FileResponse:
    path = BASE_DIR / "admin_secure.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="admin_secure.html not found")
    return FileResponse(path)
