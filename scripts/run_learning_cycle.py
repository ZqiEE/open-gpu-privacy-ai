from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import httpx


def post_json(api_url: str, path: str, payload: dict) -> dict:
    with httpx.Client(timeout=120) as client:
        response = client.post(api_url.rstrip("/") + path, json=payload)
        response.raise_for_status()
        return response.json()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run public learning export -> core scoring -> public import")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--core-path", default=os.getenv("AILOVANTA_CORE_PATH", "../ailovanta-core"))
    parser.add_argument("--work-dir", default="runtime_data/learning_cycle")
    args = parser.parse_args()

    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    events_path = work_dir / "events.json"
    result_path = work_dir / "autotruth_result.json"

    post_json(args.api_url, "/learning/export", {"output_path": str(events_path)})

    core_script = Path(args.core_path) / "scripts" / "run_autotruth.py"
    subprocess.run([sys.executable, str(core_script), str(events_path), "--output", str(result_path)], check=True)

    result = json.loads(result_path.read_text(encoding="utf-8"))
    imported = post_json(args.api_url, "/learning/runs", {"payload": result})
    print(json.dumps({"events_path": str(events_path), "result_path": str(result_path), "imported": imported}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
