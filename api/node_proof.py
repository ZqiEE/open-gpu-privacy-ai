from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
from time import time
from typing import Any

PROOF_SCHEMA = "ailovanta.node_proof.v1"


def canonical_payload(payload: dict[str, Any]) -> bytes:
    cleaned = {key: value for key, value in payload.items() if key not in {"node_proof", "proof"}}
    return json.dumps(cleaned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def proof_hash(payload: dict[str, Any], secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), canonical_payload(payload), hashlib.sha256).hexdigest()
    return "sha256:" + digest


def attach_proof(payload: dict[str, Any], node_id: str, secret: str) -> dict[str, Any]:
    body = {**payload, "node_id": payload.get("node_id") or node_id}
    body["node_proof"] = {
        "schema_version": PROOF_SCHEMA,
        "node_id": node_id,
        "signature": proof_hash(body, secret),
        "created_at": round(time(), 3),
    }
    return body


def load_node_secrets(path: str | Path | None = None) -> dict[str, str]:
    env = os.getenv("AILOVANTA_NODE_SECRETS_JSON")
    if env:
        data = json.loads(env)
        return {str(k): str(v) for k, v in data.items()}
    file_path = Path(path or os.getenv("AILOVANTA_NODE_SECRETS_PATH", "runtime_data/node_secrets.json"))
    if not file_path.exists():
        return {}
    data = json.loads(file_path.read_text(encoding="utf-8"))
    return {str(k): str(v) for k, v in data.items()}


def verify_proof(payload: dict[str, Any], secrets: dict[str, str] | None = None) -> dict[str, Any]:
    proof = payload.get("node_proof") if isinstance(payload.get("node_proof"), dict) else payload.get("proof") if isinstance(payload.get("proof"), dict) else None
    if not proof:
        return {"ok": False, "reason": "missing_proof"}
    node_id = str(proof.get("node_id") or payload.get("node_id") or "")
    if not node_id:
        return {"ok": False, "reason": "missing_node_id"}
    secret_map = secrets if secrets is not None else load_node_secrets()
    secret = secret_map.get(node_id)
    if not secret:
        return {"ok": False, "reason": "unknown_node", "node_id": node_id}
    expected = proof_hash(payload, secret)
    actual = str(proof.get("signature") or "")
    return {"ok": hmac.compare_digest(expected, actual), "reason": "valid" if hmac.compare_digest(expected, actual) else "bad_signature", "node_id": node_id}
