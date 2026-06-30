from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

SCHEMA = "ailovanta.candidate_failure_actions.v1"
DEFAULT_PATH = Path("runtime_data/candidate_failure_actions.json")

RETRAIN_BLOCKERS = {
    "missing_or_invalid_model",
    "unsupported_model_schema",
    "insufficient_training_rows",
    "insufficient_training_transitions",
    "train_loss_out_of_bounds",
}


def load_actions(path: str | Path = DEFAULT_PATH) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {"schema_version": SCHEMA, "actions": {}}
    return json.loads(target.read_text(encoding="utf-8-sig"))


def save_actions(data: dict[str, Any], path: str | Path = DEFAULT_PATH) -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    data["schema_version"] = SCHEMA
    data["updated_at"] = round(time.time(), 3)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def plan_failure_actions(
    binding: dict[str, Any],
    gate: dict[str, Any],
    *,
    action_path: str | Path = DEFAULT_PATH,
    default_max_steps: int = 32,
) -> dict[str, Any]:
    blockers = [str(item) for item in gate.get("blockers", [])]
    actions: list[dict[str, Any]] = []
    if _needs_retrain(blockers):
        action = _retrain_action(binding, gate, max_steps=default_max_steps)
        data = load_actions(action_path)
        existing = data.setdefault("actions", {}).get(action["action_id"])
        if existing and existing.get("status") in {"queued", "submitted", "done"}:
            action = existing
        else:
            data["actions"][action["action_id"]] = action
            save_actions(data, action_path)
        actions.append(action)
    return {"ok": True, "actions": actions, "action_path": str(action_path), "blockers": blockers}


def mark_action_submitted(action_id: str, submission: dict[str, Any], path: str | Path = DEFAULT_PATH) -> dict[str, Any] | None:
    data = load_actions(path)
    action = data.get("actions", {}).get(action_id)
    if not action:
        return None
    action["status"] = "submitted"
    action["submitted_at"] = round(time.time(), 3)
    action["submission"] = submission
    save_actions(data, path)
    return action


def pending_training_actions(path: str | Path = DEFAULT_PATH, limit: int = 20) -> list[dict[str, Any]]:
    actions = [item for item in load_actions(path).get("actions", {}).values() if item.get("status") == "queued" and item.get("action_type") == "training_retrain"]
    actions.sort(key=lambda item: float(item.get("created_at") or 0))
    return actions[:limit]


def action_summary(path: str | Path = DEFAULT_PATH) -> dict[str, Any]:
    data = load_actions(path)
    statuses: dict[str, int] = {}
    types: dict[str, int] = {}
    for action in data.get("actions", {}).values():
        status = str(action.get("status") or "unknown")
        action_type = str(action.get("action_type") or "unknown")
        statuses[status] = statuses.get(status, 0) + 1
        types[action_type] = types.get(action_type, 0) + 1
    return {"schema_version": data.get("schema_version") or SCHEMA, "count": len(data.get("actions", {})), "statuses": statuses, "types": types, "updated_at": data.get("updated_at")}


def _needs_retrain(blockers: list[str]) -> bool:
    return any(blocker in RETRAIN_BLOCKERS or blocker.startswith("artifact_integrity:") for blocker in blockers)


def _retrain_action(binding: dict[str, Any], gate: dict[str, Any], *, max_steps: int) -> dict[str, Any]:
    metadata = binding.get("metadata") if isinstance(binding.get("metadata"), dict) else {}
    model_eval = gate.get("model_eval") if isinstance(gate.get("model_eval"), dict) else {}
    dataset_path = str(model_eval.get("dataset_path") or "")
    dataset_uri = Path(dataset_path).resolve().as_uri() if dataset_path else ""
    blockers = [str(item) for item in gate.get("blockers", [])]
    action_id = stable_id("candidate_action_", json.dumps({"binding_id": binding.get("binding_id"), "blockers": blockers, "dataset_uri": dataset_uri}, sort_keys=True))
    request = {
        "kind": "lora_micro",
        "name": "ailovanta-retrain-" + str(binding.get("binding_id") or "candidate")[-8:],
        "dataset_uri": dataset_uri,
        "base_model": str(model_eval.get("base_model") or "ailovanta-auto-bootstrap"),
        "max_steps": max(max_steps, 64),
        "notes": "auto retrain from failed candidate gate; blockers=" + ",".join(blockers),
    }
    return {
        "schema_version": "ailovanta.candidate_failure_action.v1",
        "action_id": action_id,
        "action_type": "training_retrain",
        "status": "queued",
        "created_at": round(time.time(), 3),
        "binding_id": binding.get("binding_id"),
        "artifact_hash": binding.get("artifact_hash"),
        "source_job_id": metadata.get("source_job_id"),
        "blockers": blockers,
        "training_job_request": request,
    }


def stable_id(prefix: str, value: str) -> str:
    return prefix + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
