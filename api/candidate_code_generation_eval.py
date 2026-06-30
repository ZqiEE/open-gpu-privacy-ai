from __future__ import annotations

from typing import Any

SCHEMA = "ailovanta.candidate_code_generation_eval.v1"
SUPPORTED_CODE_GENERATION_BACKENDS = {"transformers-local", "transformers-causal-lm"}


def evaluate_candidate_code_generation(binding: dict[str, Any]) -> dict[str, Any]:
    backend_kind = str(binding.get("backend_kind") or "")
    if backend_kind not in SUPPORTED_CODE_GENERATION_BACKENDS:
        return {
            "schema_version": SCHEMA,
            "ok": False,
            "blockers": ["unsupported_code_generation_backend"],
            "backend_kind": backend_kind,
            "cases": [],
            "score": 0.0,
            "reason": "candidate backend cannot generate executable code for benchmark tasks",
        }
    return {
        "schema_version": SCHEMA,
        "ok": False,
        "blockers": ["code_generation_eval_not_configured"],
        "backend_kind": backend_kind,
        "cases": [],
        "score": 0.0,
        "reason": "code generation benchmark runner is not configured for this backend yet",
    }
