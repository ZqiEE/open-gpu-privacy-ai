from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Any

from api.verified_code_samples import sample_from_task_run

ALLOWED_COMMANDS = {
    ("python", "-m", "py_compile"),
    ("python", "-m", "pytest"),
}


@dataclass(frozen=True)
class CodeTaskRun:
    ok: bool
    task_id: str
    passed: bool
    summary: str
    report: dict[str, Any]


def run_code_instruction_task(job: dict[str, Any]) -> CodeTaskRun:
    start = time()
    payload = job.get("payload") if isinstance(job.get("payload"), dict) else {}
    task_id = str(job.get("id") or job.get("job_id") or "unknown")
    files = payload.get("files") if isinstance(payload.get("files"), dict) else {}
    commands = payload.get("commands") if isinstance(payload.get("commands"), list) else []
    max_runtime = float(payload.get("max_runtime_seconds") or 10)
    if not files:
        return _result(task_id, False, "missing files", start, [], files, task=job)
    with tempfile.TemporaryDirectory(prefix="ailovanta_code_task_") as tmp:
        root = Path(tmp).resolve()
        try:
            written = _write_files(root, files)
        except ValueError as exc:
            return _result(task_id, False, str(exc), start, [], {}, task=job)
        command_results = [_run_command(root, command, timeout=max_runtime) for command in commands]
        passed = bool(command_results) and all(item.get("ok") for item in command_results)
        summary = "code instruction task passed" if passed else "code instruction task failed"
        return _result(task_id, passed, summary, start, command_results, written, task=job)


def _write_files(root: Path, files: dict[str, Any]) -> dict[str, str]:
    written: dict[str, str] = {}
    for rel, content in files.items():
        target = (root / str(rel)).resolve()
        if root not in target.parents and target != root:
            raise ValueError("file path escapes sandbox")
        target.parent.mkdir(parents=True, exist_ok=True)
        text = str(content)
        target.write_text(text, encoding="utf-8")
        written[str(rel)] = "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
    return written


def _run_command(root: Path, command: Any, timeout: float) -> dict[str, Any]:
    if not isinstance(command, list) or not command:
        return {"ok": False, "reason": "bad_command", "command": command}
    parts = [str(part) for part in command]
    if not _allowed(parts):
        return {"ok": False, "reason": "command_not_allowed", "command": parts}
    proc = subprocess.run(parts, cwd=str(root), text=True, capture_output=True, timeout=timeout, check=False)
    return {
        "ok": proc.returncode == 0,
        "command": parts,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:],
    }


def _allowed(parts: list[str]) -> bool:
    return any(tuple(parts[: len(prefix)]) == prefix for prefix in ALLOWED_COMMANDS)


def _result(task_id: str, passed: bool, summary: str, start: float, commands: list[dict[str, Any]], files: dict[str, Any], task: dict[str, Any] | None = None) -> CodeTaskRun:
    report = {
        "schema_version": "ailovanta.code_instruction_run.v1",
        "task_id": task_id,
        "passed": passed,
        "summary": summary,
        "runtime_seconds": round(time() - start, 3),
        "commands": commands,
        "files": files,
    }
    report["report_hash"] = "sha256:" + hashlib.sha256(json.dumps(report, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    if task:
        sample = sample_from_task_run(task, report)
        if sample:
            report["verified_sample"] = sample
    return CodeTaskRun(ok=True, task_id=task_id, passed=passed, summary=summary, report=report)
