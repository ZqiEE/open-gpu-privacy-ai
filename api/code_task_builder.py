from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

TASK_SCHEMA = "ailovanta.code_instruction_task.v1"
TASK_TYPE = "code_instruction_eval"


def stable_task_id(record: dict[str, Any], prefix: str = "code_task_") -> str:
    raw = json.dumps(
        {
            "path": record.get("path"),
            "sha256": record.get("sha256"),
            "instruction": record.get("instruction"),
            "record_type": record.get("record_type"),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return prefix + hashlib.sha256(raw).hexdigest()[:16]


def task_from_instruction_record(record: dict[str, Any], candidate_files: dict[str, str] | None = None, test_command: list[str] | None = None) -> dict[str, Any]:
    path = str(record.get("path") or "task.md")
    files = {path: str(record.get("context") or record.get("text") or "")}
    for file_path, content in (candidate_files or {}).items():
        files[str(file_path)] = str(content)
    commands = test_command or _default_commands(record)
    return {
        "id": stable_task_id(record),
        "type": TASK_TYPE,
        "payload": {
            "schema_version": TASK_SCHEMA,
            "instruction": record.get("instruction"),
            "expected_response": record.get("expected_response"),
            "record_type": record.get("record_type"),
            "source_path": path,
            "language": record.get("language"),
            "files": files,
            "commands": commands,
            "max_runtime_seconds": 10,
        },
        "descriptor": {
            "schema_version": "ailovanta.job_descriptor.v1",
            "source": "instruction-first-code-ingest",
            "owner": "ailovanta-code",
        },
    }


def load_instruction_records(path: str | Path, limit: int | None = None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            item = json.loads(line)
            if item.get("training_record_kind") != "instruction":
                continue
            records.append(item)
            if limit is not None and len(records) >= limit:
                break
    return records


def build_tasks_from_corpus(corpus_path: str | Path, output_path: str | Path, limit: int | None = None) -> dict[str, Any]:
    records = load_instruction_records(corpus_path, limit=limit)
    tasks = [task_from_instruction_record(record) for record in records]
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"schema_version": "ailovanta.code_instruction_tasks.v1", "tasks": tasks}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "output": str(output), "tasks": len(tasks)}


def _default_commands(record: dict[str, Any]) -> list[list[str]]:
    path = str(record.get("path") or "")
    language = str(record.get("language") or "")
    if language == "python" or path.endswith(".py"):
        return [["python", "-m", "py_compile", path]]
    return []
