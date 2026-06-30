from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.replica_maintenance import run_replica_maintenance_loop, run_replica_maintenance_once


def main() -> int:
    parser = argparse.ArgumentParser(description="Continuously plan and fulfill local artifact replica repair tasks")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--target-node", action="append", default=[])
    parser.add_argument("--max-tasks", type=int)
    parser.add_argument("--tasks-path", default="runtime_data/replica_repair_tasks.json")
    parser.add_argument("--replica-book-path", default="runtime_data/replica_book.json")
    parser.add_argument("--storage-root", default="runtime_data/storage_replicas")
    parser.add_argument("--no-local-copy", action="store_true")
    args = parser.parse_args()
    common = {
        "tasks_path": args.tasks_path,
        "replica_book_path": args.replica_book_path,
        "storage_root": args.storage_root,
        "target_nodes": args.target_node or None,
        "max_tasks": args.max_tasks,
        "complete_local": not args.no_local_copy,
    }
    if args.loop:
        run_replica_maintenance_loop(interval=args.interval, **common)
        return 0
    out = run_replica_maintenance_once(**common)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
