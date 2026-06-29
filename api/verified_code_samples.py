from __future__ import annotations

import hashlib
import json
from pathlib import Path
from time import time
from typing import Any

SAMPLE_SCHEMA = "ailovanta.verified_code_sample.v1"
EXPORT_SCHEMA = "ailovanta.verified_code_sample_export.v1"


def stable_hash(payload: dict[str, Any]) -> str:
    body = {key: value for key, value in payload.items() if key not in {"sample_hash"}}
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def sample_from_task_run(task: dict[str, Any], report: dict[str, Any]) -> dict[str, Any] | None:
    payload = task.get("payload") if isinstance(task.get("payload"), dict) else {}
    if not report.get("passed"):
        return None
    sample = {
        "schema_version": SAMPLE_SCHEMA,
        "task_id": task.get("id") or task.get("job_id") or report.get("task_id"),
        "task_type": task.get("type") or task.get("job_type"),
        "instruction": payload.get("instruction"),
        "context_files": payload.get("files") if isinstance(payload.get("files"), dict) else {},
        "candidate_files": _candidate_files(payload),
        "expected_response": payload.get("expected_response"),
        "verification": {
            "passed": True,
            "report_hash": report.get("report_hash"),
            "commands": report.get("commands", []),
            "runtime_seconds": report.get("runtime_seconds"),
        },
        "source": {
            "record_type": payload.get("record_type"),
            "source_path": payload.get("source_path"),
            "language": payload.get("language"),
        },
        "created_at": round(time(), 3),
    }
    sample["sample_hash"] = stable_hash(sample)
    return sample


def export_samples(samples: list[dict[str, Any]], output_path: str | Path) -> dict[str, Any]:
    accepted = [sample for sample in samples if sample and sample.get("schema_version") == SAMPLE_SCHEMA]
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": EXPORT_SCHEMA, "count": len(accepted), "samples": accepted, "created_at": round(time(), 3)}
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "count": len(accepted), "output_path": str(output), "samples": accepted}


def export_samples_from_reports(reports: list[dict[str, Any]], output_path: str | Path) -> dict[str, Any]:
    samples = []
    for item in reports:
        task = item.get("task") if isinstance(item.get("task"), dict) else {}
        report = item.get("report") if isinstance(item.get("report"), dict) else item
        sample = sample_from_task_run(task, report)
        if sample:
            samples.append(sample)
    return export_samples(samples, output_path)


def _candidate_files(payload: dict[str, Any]) -> dict[str, Any]:
    files = payload.get("files") if isinstance(payload.get("files"), dict) else {}
    source_path = str(payload.get("source_path") or "")
    return {path: content for path, content in files.items() if path != source_path}
