from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException


def check_admin_token(value: str | None) -> None:
    expected = os.environ.get("AILOVANTA_ADMIN_TOKEN", "")
    if expected and not hmac.compare_digest(value or "", expected):
        raise HTTPException(status_code=401, detail="admin token required")


def admin_token_header(x_ailovanta_admin_token: str | None = Header(default=None)) -> None:
    check_admin_token(x_ailovanta_admin_token)
