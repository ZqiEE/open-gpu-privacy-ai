from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.replica_repair import ReplicaRepairStore


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan and complete artifact replica repair tasks")
    sub = parser.add_subparsers(dest="cmd", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--artifact-hash")
    plan.add_argument("--target-node", action="append", default=[])
    plan.add_argument("--max-tasks", type=int)
    list_cmd = sub.add_parser("list")
    list_cmd.add_argument("--status")
    list_cmd.add_argument("--limit", type=int, default=100)
    assign = sub.add_parser("assign")
    assign.add_argument("task_id")
    assign.add_argument("--node-id", required=True)
    complete = sub.add_parser("complete")
    complete.add_argument("task_id")
    complete.add_argument("--node-id")
    complete.add_argument("--location")
    args = parser.parse_args()
    store = ReplicaRepairStore()
    if args.cmd == "plan":
        out = store.plan_repairs(artifact_hash=args.artifact_hash, target_nodes=args.target_node or None, max_tasks=args.max_tasks)
    elif args.cmd == "list":
        out = {"tasks": store.list_tasks(status=args.status, limit=args.limit)}
    elif args.cmd == "assign":
        out = {"task": store.assign(args.task_id, args.node_id)}
    else:
        out = store.complete(args.task_id, node_id=args.node_id, location=args.location)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
