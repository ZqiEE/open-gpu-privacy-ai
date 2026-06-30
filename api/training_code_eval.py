from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "ailovanta.training_code_eval.v1"
CODE_MARKERS = ("def ", "class ", "import ", "function ", "const ", "let ", "package ", "fn ")
PYTHON_FROM_IMPORT = re.compile(r"(^|\n)\s*from\s+[\w.]+\s+import\s+", re.MULTILINE)


def evaluate_training_code_dataset(
    dataset_path: str | Path,
    *,
    min_code_records: int = 1,
    min_syntax_checks: int = 1,
    max_records: int = 512,
) -> dict[str, Any]:
    path = Path(dataset_path)
    blockers: list[str] = []
    if not path.exists():
        return {
            "schema_version": SCHEMA,
            "ok": False,
            "blockers": ["missing_dataset"],
            "dataset_path": str(path),
            "records": 0,
            "code_records": 0,
            "syntax_checks": 0,
            "syntax_failed": 0,
        }
    records = _read_rows(path, max_records=max_records)
    code_records = [row for row in records if _is_code_like(row)]
    syntax_results = [_check_python_syntax(row) for row in code_records if _should_python_parse(row)]
    syntax_failed = len([item for item in syntax_results if not item.get("passed")])
    if len(code_records) < min_code_records:
        blockers.append("no_code_records")
    if len(syntax_results) < min_syntax_checks:
        blockers.append("no_syntax_checks")
    if syntax_failed:
        blockers.append("syntax_failed")
    score_parts = [
        min(1.0, len(code_records) / max(min_code_records, 1)),
        1.0 if syntax_results and syntax_failed == 0 else 0.0,
    ]
    score = round(sum(score_parts) / len(score_parts), 4)
    return {
        "schema_version": SCHEMA,
        "ok": not blockers,
        "blockers": blockers,
        "dataset_path": str(path),
        "records": len(records),
        "code_records": len(code_records),
        "syntax_checks": len(syntax_results),
        "syntax_failed": syntax_failed,
        "score": score,
        "syntax_results": syntax_results[:20],
        "policy": {"min_code_records": min_code_records, "min_syntax_checks": min_syntax_checks},
    }


def _read_rows(path: Path, max_records: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except Exception:
                item = {"text": line}
            rows.append(item)
            if len(rows) >= max_records:
                break
    return rows


def _is_code_like(row: dict[str, Any]) -> bool:
    record_kind = str(row.get("record_kind") or row.get("training_record_kind") or "").lower()
    source_path = str(row.get("source_path") or row.get("path") or "").lower()
    text = str(row.get("text") or row.get("content") or row.get("context") or "")
    if record_kind == "code":
        return True
    if source_path.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".cpp", ".c", ".cs", ".swift", ".kt", ".rb", ".php", ".json")):
        return True
    return any(marker in text for marker in CODE_MARKERS) or bool(PYTHON_FROM_IMPORT.search(text))


def _should_python_parse(row: dict[str, Any]) -> bool:
    source_path = str(row.get("source_path") or row.get("path") or "").lower()
    record_kind = str(row.get("record_kind") or row.get("training_record_kind") or "").lower()
    text = str(row.get("text") or row.get("content") or row.get("context") or "")
    if source_path.endswith(".py"):
        return True
    return record_kind == "code" and (any(marker in text for marker in ("def ", "class ", "import ")) or bool(PYTHON_FROM_IMPORT.search(text)))


def _check_python_syntax(row: dict[str, Any]) -> dict[str, Any]:
    source_path = str(row.get("source_path") or row.get("path") or "inline.py")
    text = str(row.get("text") or row.get("content") or row.get("context") or "")
    try:
        ast.parse(text, filename=source_path)
        return {"source_path": source_path, "passed": True}
    except Exception as exc:
        return {"source_path": source_path, "passed": False, "error": str(exc)}
