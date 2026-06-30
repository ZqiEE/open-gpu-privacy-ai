from __future__ import annotations

import hashlib
import json
from pathlib import Path
from time import time
from typing import Any

FAILED_SAMPLE_SCHEMA = "ailovanta.failed_code_sample.v1"
EXPORT_SCHEMA = "ailovanta.failed_code_sample_export.v1"


def stable_hash(payload: dict[str, Any]) -> str:
    body = {key: value for key, value in payload.items() if key not in {"sample_hash"}}
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def failure_from_task_run(task: dict[str, Any], report: dict[str, Any]) -> dict[str, Any] | None:
    if report.get("passed"):
        return None
    payload = task.get("payload") if isinstance(task.get("payload"), dict) else {}
    commands = report.get("commands") if isinstance(report.get("commands"), list) else []
    failure = {
        "schema_version": FAILED_SAMPLE_SCHEMA,
        "task_id": task.get("id") or task.get("job_id") or report.get("task_id"),
        "task_type": task.get("type") or task.get("job_type"),
        "instruction": payload.get("instruction"),
        "context_files": payload.get("files") if isinstance(payload.get("files"), dict) else {},
        "candidate_files": _candidate_files(payload),
        "expected_response": payload.get("expected_response"),
        "failure": {
            "report_hash": report.get("report_hash"),
            "summary": report.get("summary"),
            "commands": commands,
            "runtime_seconds": report.get("runtime_seconds"),
        },
        "repair_prompt": repair_prompt(payload, report),
        "source": {
            "record_type": payload.get("record_type"),
            "source_path": payload.get("source_path"),
            "language": payload.get("language"),
        },
        "training_use": {
            "positive_sft": False,
            "negative_preference": True,
            "repair_task": True,
            "reward_signal": True,
        },
        "created_at": round(time(), 3),
    }
    failure["sample_hash"] = stable_hash(failure)
    return failure


def export_failures(samples: list[dict[str, Any]], output_path: str | Path) -> dict[str, Any]:
    accepted = [sample for sample in samples if sample and sample.get("schema_version") == FAILED_SAMPLE_SCHEMA]
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": EXPORT_SCHEMA, "count": len(accepted), "samples": accepted, "created_at": round(time(), 3)}
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "count": len(accepted), "output_path": str(output), "samples": accepted}


def export_failures_from_reports(reports: list[dict[str, Any]], output_path: str | Path) -> dict[str, Any]:
    failures = []
    for item in reports:
        task = item.get("task") if isinstance(item.get("task"), dict) else {}
        report = item.get("report") if isinstance(item.get("report"), dict) else item
        sample = failure_from_task_run(task, report)
        if sample:
            failures.append(sample)
    return export_failures(failures, output_path)


def repair_prompt(payload: dict[str, Any], report: dict[str, Any]) -> str:
    command_summary = []
    for item in report.get("commands", []) if isinstance(report.get("commands"), list) else []:
        command = " ".join(str(part) for part in item.get("command", [])) if isinstance(item, dict) else ""
        stderr = str(item.get("stderr") or "")[-1200:] if isinstance(item, dict) else ""
        stdout = str(item.get("stdout") or "")[-1200:] if isinstance(item, dict) else ""
        command_summary.append(f"command: {command}\nstdout:\n{stdout}\nstderr:\n{stderr}".strip())
    return "\n\n".join(
        [
            "Repair the candidate code so the executable task passes.",
            "Instruction:\n" + str(payload.get("instruction") or ""),
            "Expected response:\n" + str(payload.get("expected_response") or ""),
            "Failure evidence:\n" + ("\n\n".join(command_summary) or str(report.get("summary") or "task failed")),
        ]
    )


def _candidate_files(payload: dict[str, Any]) -> dict[str, Any]:
    files = payload.get("files") if isinstance(payload.get("files"), dict) else {}
    source_path = str(payload.get("source_path") or "")
    return {path: content for path, content in files.items() if path != source_path}
