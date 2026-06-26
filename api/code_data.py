from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from api.secret_filter import scan_text

CODE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".go", ".rs", ".cpp", ".c", ".h", ".hpp", ".cs", ".php", ".rb", ".swift", ".kt", ".kts", ".sql", ".sh", ".ps1", ".html", ".css", ".json", ".yaml", ".yml", ".toml", ".md",
}

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "dist", "build", ".next", "__pycache__", ".pytest_cache", "runtime_data"}
LICENSE_FILES = {"license", "license.md", "license.txt", "copying", "copying.txt"}
_LAST_STATS: dict[str, int] = {"scanned": 0, "accepted": 0, "skipped_secret": 0, "skipped_short": 0, "skipped_read_error": 0}


@dataclass(frozen=True)
class CodeRecord:
    source_root: str
    path: str
    language: str
    bytes: int
    sha256: str
    license_hint: str
    secret_scan_status: str
    text: str

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False, sort_keys=True)


def last_stats() -> dict[str, int]:
    return dict(_LAST_STATS)


def detect_language(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".py": "python", ".ts": "typescript", ".tsx": "typescript-react", ".js": "javascript", ".jsx": "javascript-react", ".java": "java", ".go": "go", ".rs": "rust", ".cpp": "cpp", ".c": "c", ".h": "c-header", ".hpp": "cpp-header", ".cs": "csharp", ".php": "php", ".rb": "ruby", ".swift": "swift", ".kt": "kotlin", ".kts": "kotlin", ".sql": "sql", ".sh": "shell", ".ps1": "powershell", ".html": "html", ".css": "css", ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml", ".md": "markdown",
    }.get(ext, ext.removeprefix(".") or "text")


def file_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def license_hint(root: Path) -> str:
    for child in root.iterdir() if root.exists() and root.is_dir() else []:
        if child.name.lower() in LICENSE_FILES and child.is_file():
            try:
                text = child.read_text(encoding="utf-8", errors="ignore")[:4000].lower()
            except Exception:
                return "license_file_present"
            for name in ["mit", "apache", "bsd", "mpl", "isc", "unlicense", "gpl", "lgpl", "agpl"]:
                if name in text:
                    return name
            return "license_file_present"
    return "unknown"


def iter_code_files(root: Path, max_file_bytes: int = 512_000) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in CODE_EXTENSIONS:
            continue
        try:
            if path.stat().st_size > max_file_bytes:
                continue
        except OSError:
            continue
        yield path


def build_records(root: str | Path, max_file_bytes: int = 512_000) -> list[CodeRecord]:
    base = Path(root).resolve()
    hint = license_hint(base)
    stats = {"scanned": 0, "accepted": 0, "skipped_secret": 0, "skipped_short": 0, "skipped_read_error": 0}
    records: list[CodeRecord] = []
    for path in iter_code_files(base, max_file_bytes=max_file_bytes):
        stats["scanned"] += 1
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            stats["skipped_read_error"] += 1
            continue
        clean = text.strip()
        if len(clean) < 40:
            stats["skipped_short"] += 1
            continue
        scan = scan_text(clean)
        if not scan.ok:
            stats["skipped_secret"] += 1
            continue
        rel = str(path.resolve().relative_to(base))
        records.append(
            CodeRecord(
                source_root=str(base),
                path=rel,
                language=detect_language(path),
                bytes=len(clean.encode("utf-8", errors="ignore")),
                sha256=file_hash(clean),
                license_hint=hint,
                secret_scan_status="ok",
                text=clean,
            )
        )
        stats["accepted"] += 1
    _LAST_STATS.clear()
    _LAST_STATS.update(stats)
    return records


def write_jsonl(records: list[CodeRecord], output: str | Path) -> dict:
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(record.to_json() + "\n")
    return {
        "schema_version": "ailovanta.code_corpus.v1",
        "output": str(target),
        "records": len(records),
        "bytes": sum(record.bytes for record in records),
        "languages": sorted({record.language for record in records}),
        "stats": last_stats(),
    }
