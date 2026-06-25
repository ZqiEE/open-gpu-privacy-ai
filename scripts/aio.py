from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def call(cmd: list[str]) -> dict:
    proc = subprocess.run([sys.executable, *cmd], text=True, capture_output=True)
    try:
        payload = json.loads(proc.stdout)
    except Exception:
        payload = {"ok": False, "stdout": proc.stdout, "stderr": proc.stderr}
    payload["returncode"] = proc.returncode
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Ailovanta all-in-one local owned loop")
    parser.add_argument("--core-path", default="../ailovanta-core")
    parser.add_argument("--root", default="runtime_data/local_loop")
    parser.add_argument("--secret", default="local-demo-secret")
    args = parser.parse_args()

    preflight = call(["scripts/preflight.py", "--core-path", args.core_path])
    if preflight.get("returncode") != 0 or not preflight.get("ok"):
        print(json.dumps({"ok": False, "stage": "preflight", "preflight": preflight}, ensure_ascii=False, indent=2))
        return 1

    loop = call(["scripts/local_loop.py", "--core-path", args.core_path, "--root", args.root, "--secret", args.secret])
    result_path = str(Path(args.root) / "foundation_result.json")
    final = call(["scripts/final_report.py", result_path]) if Path(result_path).exists() else {"ok": False, "reason": "missing_result", "returncode": 1}

    payload = {"ok": bool(loop.get("ok") and final.get("ok")), "preflight": preflight, "loop": loop, "final": final}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
