from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import tempfile
from copy import deepcopy
from pathlib import Path
from time import time
from typing import Any

from api.verified_code_samples import sample_from_task_run
from node_client.code_task_runner import run_code_instruction_task

REPAIR_EXPORT_SCHEMA = "ailovanta.code_repair_export.v1"
REPAIR_ATTEMPT_SCHEMA = "ailovanta.code_repair_attempt.v1"
PREFERENCE_PAIR_SCHEMA = "ailovanta.code_repair_preference_pair.v1"


def repair_failures_from_reports(
    reports: list[dict[str, Any]],
    output_path: str | Path,
    max_candidates_per_failure: int = 16,
    candidate_command: str | None = None,
    backend_ref: str | None = None,
) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    preference_pairs: list[dict[str, Any]] = []
    verified_report_items: list[dict[str, Any]] = []
    failed_count = 0
    for item in reports:
        task = item.get("task") if isinstance(item.get("task"), dict) else {}
        report = item.get("report") if isinstance(item.get("report"), dict) else item
        if report.get("passed"):
            continue
        failed_count += 1
        result = repair_failed_task(
            task,
            report,
            max_candidates=max_candidates_per_failure,
            candidate_command=candidate_command,
            backend_ref=backend_ref,
        )
        attempts.extend(result["attempts"])
        preference_pairs.extend(result["preference_pairs"])
        verified_report_items.extend(result["verified_report_items"])

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": REPAIR_EXPORT_SCHEMA,
        "failed_tasks": failed_count,
        "attempted_repairs": len(attempts),
        "repaired": len(verified_report_items),
        "attempts": attempts,
        "preference_pairs": preference_pairs,
        "created_at": round(time(), 3),
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "ok": True,
        "failed_tasks": failed_count,
        "attempted_repairs": len(attempts),
        "repaired": len(verified_report_items),
        "output_path": str(output),
        "attempts": attempts,
        "preference_pairs": preference_pairs,
        "verified_report_items": verified_report_items,
    }


def repair_failed_task(
    task: dict[str, Any],
    failed_report: dict[str, Any],
    max_candidates: int = 16,
    candidate_command: str | None = None,
    backend_ref: str | None = None,
) -> dict[str, Any]:
    if failed_report.get("passed"):
        return {"attempts": [], "preference_pairs": [], "verified_report_items": []}

    candidates = build_repair_candidate_tasks(task, failed_report, max_candidates=max_candidates, candidate_command=candidate_command, backend_ref=backend_ref)
    attempts: list[dict[str, Any]] = []
    preference_pairs: list[dict[str, Any]] = []
    verified_report_items: list[dict[str, Any]] = []
    for candidate in candidates:
        run = run_code_instruction_task(candidate["task"])
        verified_sample = sample_from_task_run(candidate["task"], run.report)
        attempt = {
            "schema_version": REPAIR_ATTEMPT_SCHEMA,
            "original_task_id": task.get("id") or task.get("job_id") or failed_report.get("task_id"),
            "attempt_task_id": candidate["task"].get("id"),
            "strategy": candidate["strategy"],
            "changed_files": candidate["changed_files"],
            "passed": bool(run.report.get("passed")),
            "report_hash": run.report.get("report_hash"),
            "summary": run.report.get("summary"),
            "verified_sample_hash": verified_sample.get("sample_hash") if verified_sample else None,
        }
        attempt["attempt_hash"] = stable_hash(attempt)
        attempts.append(attempt)
        if verified_sample:
            pair = preference_pair(task, failed_report, candidate["task"], run.report, verified_sample)
            preference_pairs.append(pair)
            verified_report_items.append({"task": candidate["task"], "report": run.report})
            break
    return {"attempts": attempts, "preference_pairs": preference_pairs, "verified_report_items": verified_report_items}


def build_repair_candidate_tasks(
    task: dict[str, Any],
    failed_report: dict[str, Any],
    max_candidates: int = 16,
    candidate_command: str | None = None,
    backend_ref: str | None = None,
) -> list[dict[str, Any]]:
    external = external_repair_candidate_tasks(task, failed_report, candidate_command, max_candidates=max_candidates, backend_ref=backend_ref) if candidate_command else []
    if len(external) >= max_candidates:
        return external[:max_candidates]
    payload = task.get("payload") if isinstance(task.get("payload"), dict) else {}
    files = payload.get("files") if isinstance(payload.get("files"), dict) else {}
    source_path = str(payload.get("source_path") or "")
    candidates: list[dict[str, Any]] = list(external)
    for file_path, content in files.items():
        if str(file_path) == source_path:
            continue
        if not _is_python_path(str(file_path)):
            continue
        for mutation in python_operator_mutations(str(content)):
            candidate_task = deepcopy(task)
            candidate_task["id"] = _repair_task_id(task, str(file_path), mutation["mutation_id"])
            candidate_task["payload"] = deepcopy(payload)
            candidate_files = dict(files)
            candidate_files[str(file_path)] = mutation["content"]
            candidate_task["payload"]["files"] = candidate_files
            candidate_task["payload"]["repair_of"] = task.get("id") or task.get("job_id") or failed_report.get("task_id")
            candidate_task["payload"]["repair_strategy"] = mutation["strategy"]
            descriptor = candidate_task.get("descriptor") if isinstance(candidate_task.get("descriptor"), dict) else {}
            candidate_task["descriptor"] = {**descriptor, "source": "ailovanta-code-repair-loop", "repair_of": candidate_task["payload"]["repair_of"]}
            candidates.append(
                {
                    "task": candidate_task,
                    "strategy": mutation["strategy"],
                    "changed_files": [str(file_path)],
                }
            )
            if len(candidates) >= max_candidates:
                return candidates
    return candidates


def external_repair_candidate_tasks(
    task: dict[str, Any],
    failed_report: dict[str, Any],
    candidate_command: str | None,
    max_candidates: int = 16,
    backend_ref: str | None = None,
) -> list[dict[str, Any]]:
    if not candidate_command:
        return []
    with tempfile.TemporaryDirectory(prefix="ailovanta_core_repair_") as tmp:
        root = Path(tmp)
        input_path = root / "failed_task_report.json"
        output_path = root / "repair_candidates.json"
        input_path.write_text(json.dumps({"task": task, "report": failed_report}, ensure_ascii=False, indent=2), encoding="utf-8")
        command = _candidate_command_parts(candidate_command, input_path, output_path, max_candidates, backend_ref=backend_ref)
        proc = subprocess.run(command, text=True, capture_output=True, check=False, timeout=30)
        if proc.returncode != 0:
            return []
        if not output_path.exists():
            return []
        try:
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return _tasks_from_external_candidates(task, failed_report, payload, max_candidates=max_candidates)


def _tasks_from_external_candidates(task: dict[str, Any], failed_report: dict[str, Any], payload: dict[str, Any], max_candidates: int) -> list[dict[str, Any]]:
    source_candidates = payload.get("candidates") if isinstance(payload.get("candidates"), list) else []
    output: list[dict[str, Any]] = []
    for index, candidate in enumerate(source_candidates):
        if not isinstance(candidate, dict):
            continue
        changed = candidate.get("files") if isinstance(candidate.get("files"), dict) else candidate.get("candidate_files")
        if not isinstance(changed, dict) or not changed:
            continue
        candidate_task = _task_with_changed_files(
            task,
            failed_report,
            changed,
            strategy=str(candidate.get("strategy") or "external_repair_candidate"),
            candidate_id=str(candidate.get("candidate_id") or f"external_{index}"),
        )
        output.append(
            {
                "task": candidate_task,
                "strategy": str(candidate.get("strategy") or "external_repair_candidate"),
                "changed_files": sorted(str(path) for path in changed),
            }
        )
        if len(output) >= max_candidates:
            break
    return output


def _task_with_changed_files(task: dict[str, Any], failed_report: dict[str, Any], changed_files: dict[str, Any], strategy: str, candidate_id: str) -> dict[str, Any]:
    payload = task.get("payload") if isinstance(task.get("payload"), dict) else {}
    files = payload.get("files") if isinstance(payload.get("files"), dict) else {}
    candidate_task = deepcopy(task)
    candidate_task["id"] = _repair_task_id(task, candidate_id, stable_hash({"strategy": strategy, "files": changed_files})[7:23])
    candidate_task["payload"] = deepcopy(payload)
    candidate_files = dict(files)
    for path, content in changed_files.items():
        candidate_files[str(path)] = str(content)
    candidate_task["payload"]["files"] = candidate_files
    candidate_task["payload"]["repair_of"] = task.get("id") or task.get("job_id") or failed_report.get("task_id")
    candidate_task["payload"]["repair_strategy"] = strategy
    descriptor = candidate_task.get("descriptor") if isinstance(candidate_task.get("descriptor"), dict) else {}
    candidate_task["descriptor"] = {**descriptor, "source": "ailovanta-code-external-repair-loop", "repair_of": candidate_task["payload"]["repair_of"]}
    return candidate_task


def _candidate_command_parts(command_template: str, input_path: Path, output_path: Path, max_candidates: int, backend_ref: str | None = None) -> list[str]:
    formatted = command_template.format(input=str(input_path), output=str(output_path), max_candidates=str(max_candidates), backend_ref=backend_ref or "")
    parts = shlex.split(formatted, posix=os.name != "nt")
    if "{output}" not in command_template and "--output" not in parts:
        parts.extend(["--output", str(output_path)])
    if "{input}" not in command_template and "--input" not in parts:
        parts.extend(["--input", str(input_path)])
    if "{max_candidates}" not in command_template and "--max-candidates" not in parts:
        parts.extend(["--max-candidates", str(max_candidates)])
    if backend_ref and "{backend_ref}" not in command_template and "--backend-ref" not in parts:
        parts.extend(["--backend-ref", backend_ref])
    return parts


def python_operator_mutations(content: str) -> list[dict[str, str]]:
    mutations: list[dict[str, str]] = []
    replacements = [
        ("-", "+"),
        ("+", "-"),
        ("*", "+"),
        ("//", "/"),
        ("/", "//"),
        ("<=", "<"),
        (">=", ">"),
        ("<", "<="),
        (">", ">="),
        ("==", "!="),
        ("!=", "=="),
    ]
    lines = content.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if not _looks_mutable_python_line(line):
            continue
        for old, new in replacements:
            replaced = _replace_first_operator(line, old, new)
            if replaced == line:
                continue
            next_lines = list(lines)
            next_lines[index] = replaced
            strategy = f"python_operator_mutation:{old}->{new}:line:{index + 1}"
            mutations.append(
                {
                    "mutation_id": stable_hash({"strategy": strategy, "line": line, "new_line": replaced})[7:23],
                    "strategy": strategy,
                    "content": "".join(next_lines),
                }
            )
    return _dedupe_mutations(mutations)


def preference_pair(
    original_task: dict[str, Any],
    failed_report: dict[str, Any],
    repaired_task: dict[str, Any],
    repaired_report: dict[str, Any],
    verified_sample: dict[str, Any],
) -> dict[str, Any]:
    pair = {
        "schema_version": PREFERENCE_PAIR_SCHEMA,
        "task_id": original_task.get("id") or original_task.get("job_id") or failed_report.get("task_id"),
        "chosen_task_id": repaired_task.get("id"),
        "rejected_report_hash": failed_report.get("report_hash"),
        "chosen_report_hash": repaired_report.get("report_hash"),
        "chosen_sample_hash": verified_sample.get("sample_hash"),
        "reward": {
            "rejected_test_passed": False,
            "chosen_test_passed": True,
            "score_delta": 1.0,
        },
        "training_use": {
            "positive_sft": True,
            "preference": True,
            "repair_task": True,
            "reward_signal": True,
        },
        "created_at": round(time(), 3),
    }
    pair["pair_hash"] = stable_hash(pair)
    return pair


def stable_hash(payload: dict[str, Any]) -> str:
    body = {key: value for key, value in payload.items() if not str(key).endswith("_hash")}
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _repair_task_id(task: dict[str, Any], file_path: str, mutation_id: str) -> str:
    base = str(task.get("id") or task.get("job_id") or "code_task")
    raw = json.dumps({"base": base, "file": file_path, "mutation": mutation_id}, sort_keys=True).encode("utf-8")
    return base + "_repair_" + hashlib.sha256(raw).hexdigest()[:10]


def _is_python_path(path: str) -> bool:
    return path.endswith(".py")


def _looks_mutable_python_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return False
    return stripped.startswith("return ") or "=" in stripped or stripped.startswith("if ") or stripped.startswith("elif ")


def _replace_first_operator(line: str, old: str, new: str) -> str:
    pattern = rf"(?<![<>=!]){re.escape(old)}(?![<>=!])" if old in {"<", ">", "=", "!"} else re.escape(old)
    return re.sub(pattern, new, line, count=1)


def _dedupe_mutations(mutations: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    output = []
    for mutation in mutations:
        key = mutation["content"]
        if key in seen:
            continue
        seen.add(key)
        output.append(mutation)
    return output
