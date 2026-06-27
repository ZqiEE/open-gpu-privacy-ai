from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def load_tasks(path: str) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    p = Path(path)
    if not p.exists():
        return tasks
    if p.suffix == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else data.get("tasks", [])
    with p.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                tasks.append(json.loads(line))
            except Exception:
                pass
    return tasks


def read_candidate(candidate_dir: Path, task: dict[str, Any]) -> str:
    task_id = str(task.get("task_id") or task.get("id") or "task").replace("/", "_")
    for name in [f"{task_id}.py", "solution.py", "completion.py"]:
        path = candidate_dir / name
        if path.exists():
            return path.read_text(encoding="utf-8", errors="ignore")
    return str(task.get("completion") or "")


def run_task(candidate_dir: Path, task: dict[str, Any], timeout: int) -> dict[str, Any]:
    code = read_candidate(candidate_dir, task)
    test = str(task.get("test") or "")
    entry = str(task.get("entry_point") or "")
    if not code or not test:
        return {"task_id": task.get("task_id") or task.get("id"), "passed": False, "reason": "missing code or test"}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "candidate.py").write_text(code, encoding="utf-8")
        runner = root / "run_eval.py"
        runner.write_text("from candidate import *\n" + test + "\n", encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, str(runner)], cwd=str(root), capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"task_id": task.get("task_id") or task.get("id"), "entry_point": entry, "passed": False, "reason": "timeout"}
    return {"task_id": task.get("task_id") or task.get("id"), "entry_point": entry, "passed": proc.returncode == 0, "stdout": proc.stdout[-1000:], "stderr": proc.stderr[-1000:]}


def run_humaneval_lite(candidate_dir: str, task_path: str, timeout: int = 5) -> dict[str, Any]:
    tasks = load_tasks(task_path)
    root = Path(candidate_dir)
    results = [run_task(root, task, timeout) for task in tasks]
    passed = sum(1 for item in results if item.get("passed"))
    score = round(passed / max(len(results), 1), 4)
    return {"score": score, "passed": bool(results) and score >= 0.5, "passed_count": passed, "total": len(results), "results": results}
