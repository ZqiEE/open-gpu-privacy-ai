from __future__ import annotations

import argparse
import json
import subprocess
import sys

from api.preflight import check


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight then run local loop")
    parser.add_argument("--core-path", default="../ailovanta-core")
    parser.add_argument("--root", default="runtime_data/local_loop")
    parser.add_argument("--secret", default="local-demo-secret")
    args = parser.parse_args()
    preflight = check(args.core_path)
    if not preflight.get("ok"):
        print(json.dumps({"ok": False, "stage": "preflight", "preflight": preflight}, ensure_ascii=False, indent=2))
        return 1
    proc = subprocess.run([sys.executable, "scripts/local_loop.py", "--core-path", args.core_path, "--root", args.root, "--secret", args.secret], check=False, text=True, capture_output=True)
    try:
        payload = json.loads(proc.stdout)
    except Exception:
        payload = {"ok": False, "stdout": proc.stdout, "stderr": proc.stderr}
    print(json.dumps({"ok": proc.returncode == 0 and bool(payload.get("ok")), "preflight": preflight, "local_loop": payload}, ensure_ascii=False, indent=2))
    return 0 if proc.returncode == 0 and payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
