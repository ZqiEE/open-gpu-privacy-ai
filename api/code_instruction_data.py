from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from api.code_data import SKIP_DIRS, detect_language
from api.secret_filter import scan_text

INSTRUCTION_EXTENSIONS = {".md", ".rst", ".txt", ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".yaml", ".yml", ".json", ".toml"}
DOC_HINTS = {"readme", "docs", "doc", "guide", "tutorial", "examples", "example", "spec", "design", "adr", "architecture", ".github"}
TEST_HINTS = {"test", "tests", "__tests__", "spec", "e2e", "integration"}
ISSUE_HINTS = {"issue_template", "pull_request_template", "bug_report", "feature_request"}
_LAST_STATS: dict[str, int] = {"scanned": 0, "accepted": 0, "skipped_secret": 0, "skipped_short": 0, "skipped_irrelevant": 0, "skipped_read_error": 0}


@dataclass(frozen=True)
class CodeInstructionRecord:
    source_root: str
    path: str
    record_type: str
    language: str
    bytes: int
    sha256: str
    secret_scan_status: str
    instruction: str
    context: str
    expected_response: str

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False, sort_keys=True)


def last_stats() -> dict[str, int]:
    return dict(_LAST_STATS)


def hash_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def iter_instruction_files(root: Path, max_file_bytes: int = 512_000) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file() or path.suffix.lower() not in INSTRUCTION_EXTENSIONS:
            continue
        try:
            if path.stat().st_size > max_file_bytes:
                continue
        except OSError:
            continue
        rel_parts = {part.lower() for part in path.relative_to(root).parts}
        name = path.name.lower()
        if not (rel_parts & DOC_HINTS or rel_parts & TEST_HINTS or any(hint in name for hint in DOC_HINTS | TEST_HINTS | ISSUE_HINTS)):
            continue
        yield path


def classify(path: Path, root: Path) -> str:
    rel_parts = {part.lower() for part in path.relative_to(root).parts}
    name = path.name.lower()
    if rel_parts & TEST_HINTS or any(hint in name for hint in TEST_HINTS):
        return "test_spec"
    if any(hint in name for hint in ISSUE_HINTS) or ".github" in rel_parts:
        return "issue_or_pr_template"
    return "documentation"


def make_instruction(record_type: str, rel_path: str, language: str) -> str:
    if record_type == "test_spec":
        return f"Implement or modify the repository code so the tests/specification in {rel_path} pass. Explain the required behavior before coding."
    if record_type == "issue_or_pr_template":
        return f"Use the repository template in {rel_path} to understand how to describe, triage, and solve development tasks."
    return f"Use the repository documentation in {rel_path} to explain the API, architecture, setup, or implementation requirements."


def make_expected(record_type: str) -> str:
    if record_type == "test_spec":
        return "A correct answer should infer required behavior from the test, propose the implementation, and preserve existing behavior."
    if record_type == "issue_or_pr_template":
        return "A correct answer should turn the template into a clear engineering task with reproducible context and acceptance criteria."
    return "A correct answer should summarize the documented behavior and translate it into actionable implementation guidance."


def build_instruction_records(root: str | Path, max_file_bytes: int = 512_000) -> list[CodeInstructionRecord]:
    base = Path(root).resolve()
    stats = {"scanned": 0, "accepted": 0, "skipped_secret": 0, "skipped_short": 0, "skipped_irrelevant": 0, "skipped_read_error": 0}
    records: list[CodeInstructionRecord] = []
    for path in iter_instruction_files(base, max_file_bytes=max_file_bytes):
        stats["scanned"] += 1
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            stats["skipped_read_error"] += 1
            continue
        clean = text.strip()
        if len(clean) < 80:
            stats["skipped_short"] += 1
            continue
        scan = scan_text(clean)
        if not scan.ok:
            stats["skipped_secret"] += 1
            continue
        rel = str(path.resolve().relative_to(base))
        record_type = classify(path, base)
        language = detect_language(path)
        records.append(
            CodeInstructionRecord(
                source_root=str(base),
                path=rel,
                record_type=record_type,
                language=language,
                bytes=len(clean.encode("utf-8", errors="ignore")),
                sha256=hash_text(clean),
                secret_scan_status="ok",
                instruction=make_instruction(record_type, rel, language),
                context=clean,
                expected_response=make_expected(record_type),
            )
        )
        stats["accepted"] += 1
    _LAST_STATS.clear()
    _LAST_STATS.update(stats)
    return records
