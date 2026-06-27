from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


CODE_CASES = [
    {"id": "reverse", "entry": "solution.py", "test": "from solution import reverse_string\nassert reverse_string('abc') == 'cba'"},
    {"id": "sum_numbers", "entry": "solution.py", "test": "from solution import sum_numbers\nassert sum_numbers([1, 2, 3]) == 6"},
]


def run_pytest_path(path: str, timeout: int = 60) -> dict[str, Any]:
    root = Path(path)
    if not root.exists():
        return {"passed": False, "score": 0.0, "reason": "path not found", "path": str(root)}
    cmd = [sys.executable, "-m", "pytest", str(root), "-q"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"passed": False, "score": 0.0, "reason": "pytest timeout", "path": str(root)}
    passed = proc.returncode == 0
    return {"passed": passed, "score": 1.0 if passed else 0.0, "returncode": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:], "path": str(root)}


def run_static_code_checks(path: str) -> dict[str, Any]:
    root = Path(path)
    files = list(root.rglob("*.py")) if root.exists() else []
    syntax_ok = 0
    details = []
    for file in files[:100]:
        try:
            compile(file.read_text(encoding="utf-8", errors="ignore"), str(file), "exec")
            syntax_ok += 1
            details.append({"file": str(file), "syntax": True})
        except Exception as exc:
            details.append({"file": str(file), "syntax": False, "error": str(exc)})
    score = round(syntax_ok / max(len(files[:100]), 1), 4) if files else 0.0
    return {"passed": bool(files) and score >= 0.8, "score": score, "files_checked": len(files[:100]), "details": details[:20]}


def write_benchmark_report(path: str, output_path: str | None = None) -> dict[str, Any]:
    static_result = run_static_code_checks(path)
    pytest_result = run_pytest_path(path) if (Path(path) / "tests").exists() else {"passed": False, "score": 0.0, "reason": "no tests directory"}
    score = round(static_result["score"] * 0.4 + pytest_result["score"] * 0.6, 4)
    report = {"score": score, "passed": score >= 0.5, "static": static_result, "pytest": pytest_result}
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
