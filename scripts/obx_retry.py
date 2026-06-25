from __future__ import annotations

import argparse
import json

from api.outbox_run import retry_latest


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--plan", required=True)
    p.add_argument("--core", default="../ailovanta-core")
    p.add_argument("--out", default="runtime_data/parcels/foundation_result.json")
    a = p.parse_args()
    data = retry_latest(plan_path=a.plan, core_path=a.core, result_output=a.out)
    print(json.dumps({"ok": bool(data and data.get("ok")), "run": data}, ensure_ascii=False, indent=2))
    return 0 if data and data.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
