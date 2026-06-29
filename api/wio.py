from __future__ import annotations

import hashlib
import hmac
import json
import os
from time import time
from typing import Any

from api.node_proof import attach_proof, verify_proof
from api.wc import make_result, make_task

TASK_PROOF_SCHEMA = "ailovanta.task_proof.v1"


def task_signing_secret() -> str:
    return os.getenv("AILOVANTA_TASK_SIGNING_SECRET", "local-testnet-task-secret")


def canonical_task(task: dict[str, Any]) -> bytes:
    cleaned = {key: value for key, value in task.items() if key != "task_proof"}
    return json.dumps(cleaned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def task_hash(task: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_task(task)).hexdigest()


def task_signature(task: dict[str, Any], secret: str | None = None) -> str:
    digest = hmac.new((secret or task_signing_secret()).encode("utf-8"), canonical_task(task), hashlib.sha256).hexdigest()
    return "sha256:" + digest


def sign_task(task: dict[str, Any], issuer: str = "gateway", secret: str | None = None) -> dict[str, Any]:
    body = dict(task)
    body["task_proof"] = {
        "schema_version": TASK_PROOF_SCHEMA,
        "issuer": issuer,
        "task_hash": task_hash(body),
        "signature": task_signature(body, secret),
        "created_at": round(time(), 3),
    }
    return body


def task_from_envelope(envelope: dict[str, Any]) -> dict[str, Any]:
    if isinstance(envelope.get("task"), dict):
        return envelope["task"]
    return envelope


def verify_task_envelope(envelope: dict[str, Any], secret: str | None = None) -> dict[str, Any]:
    task = task_from_envelope(envelope)
    proof = task.get("task_proof") if isinstance(task.get("task_proof"), dict) else None
    if not proof:
        return {"ok": False, "reason": "missing_task_proof", "task": task}
    if proof.get("schema_version") != TASK_PROOF_SCHEMA:
        return {"ok": False, "reason": "bad_task_proof_schema", "task": task, "proof": proof}
    expected_hash = task_hash(task)
    if proof.get("task_hash") != expected_hash:
        return {"ok": False, "reason": "task_hash_mismatch", "task": task, "proof": proof, "expected_task_hash": expected_hash}
    expected_signature = task_signature(task, secret)
    ok = hmac.compare_digest(str(proof.get("signature") or ""), expected_signature)
    return {
        "ok": ok,
        "reason": "valid" if ok else "bad_task_signature",
        "task_id": task.get("task_id"),
        "node_id": task.get("node_id"),
        "task_hash": expected_hash,
        "proof": proof,
    }


def task_envelope(plan: dict[str, Any], node_id: str, input_uri: str, output_uri: str) -> dict[str, Any]:
    return {"kind": "worker_task", "task": sign_task(make_task(plan, node_id, input_uri, output_uri))}


def signed_result(payload: dict[str, Any], node_id: str, secret: str) -> dict[str, Any]:
    result = make_result({**payload, "node_id": node_id})
    return attach_proof(result, node_id=node_id, secret=secret)


def result_shape(payload: dict[str, Any]) -> dict[str, Any]:
    for key in ["task_id", "node_id", "checkpoint_uri", "checkpoint_hash", "node_proof"]:
        if not payload.get(key):
            return {"ok": False, "reason": f"missing_{key}"}
    if not str(payload.get("checkpoint_hash", "")).startswith("sha256:"):
        return {"ok": False, "reason": "bad_checkpoint_hash"}
    if not str(payload.get("checkpoint_uri", "")).startswith(("s3://", "ipfs://", "file://", "http://", "https://")):
        return {"ok": False, "reason": "bad_checkpoint_uri"}
    return {"ok": True}


def verify_result(payload: dict[str, Any], task_envelope: dict[str, Any] | None = None) -> dict[str, Any]:
    shape = result_shape(payload)
    if not shape.get("ok"):
        return {"ok": False, "shape": shape, "proof": None, "result": payload}
    task_check = None
    if task_envelope is not None:
        task_check = verify_task_envelope(task_envelope)
        task = task_from_envelope(task_envelope)
        if not task_check.get("ok"):
            return {"ok": False, "shape": shape, "proof": None, "task": task_check, "result": payload}
        if str(task.get("task_id")) != str(payload.get("task_id")):
            return {"ok": False, "shape": shape, "proof": None, "task": task_check, "result": payload, "reason": "task_id_mismatch"}
        if str(task.get("node_id")) != str(payload.get("node_id")):
            return {"ok": False, "shape": shape, "proof": None, "task": task_check, "result": payload, "reason": "node_id_mismatch"}
    proof = verify_proof(payload)
    return {"ok": bool(proof.get("ok") or proof.get("valid")), "shape": shape, "proof": proof, "task": task_check, "result": payload}
