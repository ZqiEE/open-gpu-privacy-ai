from __future__ import annotations

import argparse
import json

from api.ckpt_merge import merge_ckpts
from api.didx import for_plan, save, scan


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--plan-id", required=True)
    p.add_argument("--model-id", default="ailovanta-foundation")
    p.add_argument("--version", default="v0.1")
    p.add_argument("--stage", default="build")
    p.add_argument("--no-scan", action="store_true")
    p.add_argument("--allow-unverified", action="store_true")
    args = p.parse_args()
    if not args.no_scan:
        save(scan())
    items = for_plan(args.plan_id, only_ok=not args.allow_unverified)
    plan = {"plan_id": args.plan_id, "model_id": args.model_id, "version": args.version, "stage": args.stage}
    result = merge_ckpts(plan, items)
    print(json.dumps({"used_index_items": len(items), "checkpoint": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
