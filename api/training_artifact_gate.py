from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from api.artifact_integrity import verify_artifact_uri
from api.candidate_code_generation_eval import evaluate_candidate_code_generation
from api.runtime_ref import to_local_path
from api.route_health import RouteHealth
from api.training_code_eval import evaluate_training_code_dataset


def evaluate_training_artifact_binding(
    binding: dict[str, Any],
    *,
    model_path: str | Path,
    replica_book_path: str | Path = "runtime_data/replica_book.json",
    min_rows: int = 1,
    min_transitions: int = 1,
    max_train_loss: float = 20.0,
    min_code_records: int = 1,
    min_code_syntax_checks: int = 1,
) -> dict[str, Any]:
    blockers: list[str] = []
    code_eval = None
    backend_kind = str(binding.get("backend_kind") or "")
    model = _read_model(model_path)
    code_generation_eval = evaluate_candidate_code_generation(binding)
    if not code_generation_eval.get("ok"):
        blockers.extend("code_generation:" + str(item) for item in code_generation_eval.get("blockers", []))
    if backend_kind == "lightweight-ngram":
        if not model:
            blockers.append("missing_or_invalid_model")
        else:
            blockers.extend(
                _evaluate_lightweight_model(
                    model,
                    min_rows=min_rows,
                    min_transitions=min_transitions,
                    max_train_loss=max_train_loss,
                )
            )
            code_eval, code_blockers = _evaluate_dataset_from_model(model, min_code_records=min_code_records, min_code_syntax_checks=min_code_syntax_checks)
            blockers.extend(code_blockers)
    elif backend_kind in {"transformers-local", "transformers-causal-lm"}:
        model_blockers, model = _evaluate_transformers_model(binding, model)
        blockers.extend(model_blockers)
        code_eval, code_blockers = _evaluate_dataset_from_model(model or {}, min_code_records=min_code_records, min_code_syntax_checks=min_code_syntax_checks)
        blockers.extend(code_blockers)
    else:
        blockers.append("unsupported_training_artifact_backend")

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
        "code_eval": code_eval,
        "code_generation_eval": code_generation_eval,
        "artifact_integrity": integrity,
        "artifact_distribution": distribution,
        "policy": {
            "min_rows": min_rows,
            "min_transitions": min_transitions,
            "max_train_loss": max_train_loss,
            "min_code_records": min_code_records,
            "min_code_syntax_checks": min_code_syntax_checks,
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


def _evaluate_lightweight_model(
    model: dict[str, Any],
    *,
    min_rows: int,
    min_transitions: int,
    max_train_loss: float,
) -> list[str]:
    blockers: list[str] = []
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
    return blockers


def _evaluate_transformers_model(binding: dict[str, Any], record: dict[str, Any] | None) -> tuple[list[str], dict[str, Any] | None]:
    blockers: list[str] = []
    if not record:
        blockers.append("missing_or_invalid_training_output")
        record = {}
    if record.get("schema") != "ailovanta.model_output.v1":
        blockers.append("unsupported_model_output_schema")
    if str(record.get("kind") or "") == "training_failed":
        blockers.append("training_output_failed")
    backend = str(((record.get("metrics") or {}) if isinstance(record.get("metrics"), dict) else {}).get("backend") or "")
    if backend not in {"transformers", "lora", "qlora"}:
        blockers.append("unsupported_real_training_backend")
    backend_ref = str(binding.get("backend_ref") or binding.get("checkpoint_uri") or "")
    path = to_local_path(backend_ref)
    if path is None:
        blockers.append("backend_ref_unsupported")
    elif not path.exists():
        blockers.append("backend_ref_not_found")
    elif not path.is_dir():
        blockers.append("backend_ref_not_model_directory")
    return blockers, record


def _evaluate_dataset_from_model(
    model: dict[str, Any],
    *,
    min_code_records: int,
    min_code_syntax_checks: int,
) -> tuple[dict[str, Any] | None, list[str]]:
    dataset_path = _resolve_dataset_path(str(model.get("dataset_path") or model.get("dataset_uri") or model.get("data_path") or ""))
    if not dataset_path:
        return None, ["code_eval:missing_dataset_path"]
    code_eval = evaluate_training_code_dataset(str(dataset_path), min_code_records=min_code_records, min_syntax_checks=min_code_syntax_checks)
    blockers = [] if code_eval.get("ok") else ["code_eval:" + str(item) for item in code_eval.get("blockers", [])]
    return code_eval, blockers


def _resolve_dataset_path(value: str) -> Path | None:
    if not value:
        return None
    if value.startswith("file://"):
        return to_local_path(value)
    if value.startswith("local://"):
        return Path(value.removeprefix("local://"))
    if "://" in value:
        return None
    return Path(value)


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
        "dataset_path": model.get("dataset_path") or model.get("dataset_uri") or model.get("data_path"),
        "kind": model.get("kind"),
        "backend": ((model.get("metrics") or {}) if isinstance(model.get("metrics"), dict) else {}).get("backend"),
    }


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None
