from __future__ import annotations

import argparse
import json

from api.ckpt_merge import merge_ckpts


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--plan-id", required=True)
    p.add_argument("--model-id", default="ailovanta-foundation")
    p.add_argument("--version", default="v0.1")
    p.add_argument("--stage", default="build")
    args = p.parse_args()
    plan = {"plan_id": args.plan_id, "model_id": args.model_id, "version": args.version, "stage": args.stage}
    print(json.dumps(merge_ckpts(plan), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
