from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any


class NodeTokenStore:
    def __init__(self, path: str | Path = "runtime_data/node_tokens.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def all(self) -> dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def issue(self, node_id: str) -> dict[str, str]:
        token = hashlib.sha256(os.urandom(32)).hexdigest()
        data = self.all()
        data[node_id] = {"token_hash": hash_token(token)}
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"node_id": node_id, "token": token, "token_preview": token[:8] + "..."}

    def verify(self, token: str | None, node_id: str | None = None) -> bool:
        if not token:
            return False
        data = self.all()
        if node_id and node_id in data:
            return hmac.compare_digest(data[node_id].get("token_hash", ""), hash_token(token))
        digest = hash_token(token)
        return any(hmac.compare_digest(item.get("token_hash", ""), digest) for item in data.values())


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def current_secret() -> str:
    return os.environ.get("AILOVANTA_NODE_TOKEN", "")


def require_token(token: str | None, node_id: str | None = None) -> None:
    secret = current_secret()
    if secret and hmac.compare_digest(token or "", secret):
        return
    if NodeTokenStore().verify(token, node_id):
        return
    if secret or NodeTokenStore().all():
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
