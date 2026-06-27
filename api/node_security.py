from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any


def current_secret() -> str:
    return os.environ.get("AILOVANTA_NODE_TOKEN", "")


def require_token(token: str | None) -> None:
    secret = current_secret()
    if secret and not hmac.compare_digest(token or "", secret):
        raise PermissionError("invalid node token")


def sign_body(body: dict[str, Any], secret: str | None = None) -> str:
    key = (secret if secret is not None else current_secret()).encode("utf-8")
    raw = json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hmac.new(key, raw, hashlib.sha256).hexdigest()


def save_node_token(path: str | Path = "runtime_data/node_token.txt") -> dict[str, str]:
    token = os.environ.get("AILOVANTA_NODE_TOKEN") or hashlib.sha256(os.urandom(32)).hexdigest()
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(token, encoding="utf-8")
    return {"path": str(p), "token_preview": token[:8] + "..."}
