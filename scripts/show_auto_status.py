from __future__ import annotations

import argparse
import json

from api.autonomous_loop import AutonomousLoop


def main() -> int:
    parser = argparse.ArgumentParser(description="Show latest autonomous loop status")
    parser.add_argument("--root", default="runtime_data/autonomous_loop")
    args = parser.parse_args()
    run = AutonomousLoop(root=args.root).latest_run()
    if not run:
        print(json.dumps({"ok": False, "reason": "no runs"}, ensure_ascii=False, indent=2))
        return 1
    after = run.get("doctor_after_prepare") or {}
    payload = {
        "ok": bool(after.get("ok")),
        "run_id": run.get("run_id"),
        "model_key": run.get("model_key"),
        "blockers": after.get("blockers"),
        "prepare_ok": bool((run.get("runtime_prepare") or {}).get("ok")),
        "created_at": run.get("created_at"),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
