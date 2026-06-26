from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from api.ckpt_merge import to_path
from api.sqlite_utils import connect_sqlite


def parse_item(text: str) -> dict[str, Any] | None:
    try:
        data = json.loads(text)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    if not data.get("delta_ref") or not data.get("plan_id"):
        return None
    return data


def hash_ref(ref: str) -> str | None:
    path = to_path(ref)
    if path is None or not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def scan(db_path: str | Path = "runtime_data/scheduler.sqlite3") -> list[dict[str, Any]]:
    path = Path(db_path)
    if not path.exists():
        return []
    with connect_sqlite(path) as conn:
        rows = conn.execute("SELECT result_id, node_id, job_id, status, output_summary, submitted_at FROM results ORDER BY submitted_at ASC").fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        raw = dict(row)
        item = parse_item(raw.get("output_summary") or "")
        if not item:
            continue
        actual = hash_ref(str(item.get("delta_ref")))
        expected = item.get("delta_hash")
        out.append(
            {
                "result_id": raw["result_id"],
                "node_id": raw["node_id"],
                "job_id": raw["job_id"],
                "status": raw["status"],
                "submitted_at": raw["submitted_at"],
                "plan_id": item.get("plan_id"),
                "model_id": item.get("model_id"),
                "version": item.get("version"),
                "stage": item.get("stage"),
                "token_count": item.get("token_count"),
                "delta_ref": item.get("delta_ref"),
                "delta_hash": expected,
                "actual_hash": actual,
                "hash_ok": bool(actual and expected and actual == expected),
                "train_loss": item.get("train_loss"),
                "initial_loss": item.get("initial_loss"),
                "device": item.get("device"),
            }
        )
    return out


def save(items: list[dict[str, Any]], path: str | Path = "runtime_data/didx.json") -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": "ailovanta.didx.v1", "count": len(items), "items": items}
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def load(path: str | Path = "runtime_data/didx.json") -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {"schema_version": "ailovanta.didx.v1", "count": 0, "items": []}
    return json.loads(target.read_text(encoding="utf-8"))


def for_plan(plan_id: str, only_ok: bool = True) -> list[dict[str, Any]]:
    items = [item for item in load().get("items", []) if item.get("plan_id") == plan_id]
    return [item for item in items if item.get("hash_ok")] if only_ok else items
