from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from api.artifact_integrity import verify_artifact_uri
from api.route_health import RouteHealth


def evaluate_training_artifact_binding(
    binding: dict[str, Any],
    *,
    model_path: str | Path,
    replica_book_path: str | Path = "runtime_data/replica_book.json",
    min_rows: int = 1,
    min_transitions: int = 1,
    max_train_loss: float = 20.0,
) -> dict[str, Any]:
    blockers: list[str] = []
    model = _read_model(model_path)
    if not model:
        blockers.append("missing_or_invalid_model")
    else:
        if model.get("schema") != "ailovanta.lightweight_ngram.v1":
            blockers.append("unsupported_model_schema")
        rows = int(model.get("rows") or 0)
        transitions = int(model.get("transitions") or 0)
        train_loss = _float(model.get("train_loss"))
        if rows < min_rows:
            blockers.append("insufficient_training_rows")
        if transitions < min_transitions:
            blockers.append("insufficient_training_transitions")
        if train_loss is None or not math.isfinite(train_loss) or train_loss > max_train_loss:
            blockers.append("train_loss_out_of_bounds")

    integrity = verify_artifact_uri(str(binding.get("backend_ref") or binding.get("checkpoint_uri") or ""), str(binding.get("artifact_hash") or ""))
    if not integrity.get("ok"):
        blockers.append("artifact_integrity:" + str(integrity.get("reason")))

    distribution = RouteHealth(replica_book_path=replica_book_path).check_artifact_distribution(binding)
    if not distribution.get("ok"):
        blockers.extend("artifact_distribution:" + str(item) for item in distribution.get("blockers", []))

    return {
        "schema_version": "ailovanta.training_artifact_gate.v1",
        "ok": not blockers,
        "decision": "promote_active" if not blockers else "keep_candidate",
        "blockers": sorted(set(blockers)),
        "model_eval": _compact_model(model),
        "artifact_integrity": integrity,
        "artifact_distribution": distribution,
        "policy": {
            "min_rows": min_rows,
            "min_transitions": min_transitions,
            "max_train_loss": max_train_loss,
        },
    }


def _read_model(path: str | Path) -> dict[str, Any] | None:
    target = Path(path)
    if not target.exists() or not target.is_file():
        return None
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return None


def _compact_model(model: dict[str, Any] | None) -> dict[str, Any]:
    if not model:
        return {"ok": False}
    return {
        "ok": True,
        "schema": model.get("schema"),
        "rows": model.get("rows"),
        "transitions": model.get("transitions"),
        "train_loss": model.get("train_loss"),
        "base_model": model.get("base_model"),
        "dataset_path": model.get("dataset_path"),
    }


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None
