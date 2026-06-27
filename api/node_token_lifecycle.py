from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from time import time
from typing import Any


PATH = Path("runtime_data/node_tokens.json")


def read_tokens() -> dict[str, Any]:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    if not PATH.exists():
        PATH.write_text("{}", encoding="utf-8")
    try:
        return json.loads(PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_tokens(data: dict[str, Any]) -> None:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_token() -> str:
    return hashlib.sha256(os.urandom(32)).hexdigest()


def rotate_node_token(node_id: str) -> dict[str, str]:
    token = new_token()
    data = read_tokens()
    old = data.get(node_id, {})
    data[node_id] = {
        "token_hash": hash_token(token),
        "status": "active",
        "issued_at": old.get("issued_at") or time(),
        "rotated_at": time(),
        "revoked_at": None,
    }
    write_tokens(data)
    return {"node_id": node_id, "token": token, "token_preview": token[:8] + "..."}


def revoke_node_token(node_id: str) -> dict[str, Any]:
    data = read_tokens()
    item = data.get(node_id)
    if not item:
        return {"node_id": node_id, "revoked": False, "reason": "not found"}
    item["status"] = "revoked"
    item["revoked_at"] = time()
    data[node_id] = item
    write_tokens(data)
    return {"node_id": node_id, "revoked": True}
