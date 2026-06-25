from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
from time import time
from typing import Any

from api.node_trust import NodeTrustStore

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


def proof_parts(payload: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    proof = payload.get("node_proof") if isinstance(payload.get("node_proof"), dict) else payload.get("proof") if isinstance(payload.get("proof"), dict) else None
    if not proof:
        return None, ""
    return proof, str(proof.get("node_id") or payload.get("node_id") or "")


def verify_with_secrets(payload: dict[str, Any], secrets: dict[str, str]) -> dict[str, Any]:
    proof, node_id = proof_parts(payload)
    if not proof:
        return {"ok": False, "reason": "missing_proof"}
    if not node_id:
        return {"ok": False, "reason": "missing_node_id"}
    secret = secrets.get(node_id)
    if not secret:
        return {"ok": False, "reason": "unknown_node", "node_id": node_id}
    expected = proof_hash(payload, secret)
    actual = str(proof.get("signature") or "")
    ok = hmac.compare_digest(expected, actual)
    return {"ok": ok, "reason": "valid" if ok else "bad_signature", "node_id": node_id, "source": "provided_secrets"}


def verify_with_store(payload: dict[str, Any], store: NodeTrustStore | None = None) -> dict[str, Any]:
    proof, node_id = proof_parts(payload)
    if not proof:
        return {"ok": False, "reason": "missing_proof"}
    if not node_id:
        return {"ok": False, "reason": "missing_node_id"}
    item = (store or NodeTrustStore()).get(node_id)
    if not item:
        return {"ok": False, "reason": "unknown_node", "node_id": node_id, "source": "trust_store"}
    if item.get("status") != "active":
        return {"ok": False, "reason": "node_not_active", "node_id": node_id, "status": item.get("status"), "source": "trust_store"}
    actual = str(proof.get("signature") or "")
    # The store intentionally keeps only the secret hash. To verify an HMAC signature, the plain secret must be supplied
    # through the temporary secret map. The store still acts as the trust/status registry.
    return {"ok": False, "reason": "secret_required", "node_id": node_id, "source": "trust_store", "trust_score": item.get("trust_score")}


def verify_proof(payload: dict[str, Any], secrets: dict[str, str] | None = None) -> dict[str, Any]:
    if secrets is not None:
        return verify_with_secrets(payload, secrets)
    secret_map = load_node_secrets()
    if secret_map:
        result = verify_with_secrets(payload, secret_map)
        if result.get("ok"):
            item = NodeTrustStore().get(result["node_id"])
            if item and item.get("status") != "active":
                return {"ok": False, "reason": "node_not_active", "node_id": result["node_id"], "status": item.get("status"), "source": "trust_store"}
            if item:
                result["trust_score"] = item.get("trust_score")
            return result
    return verify_with_store(payload)
