from __future__ import annotations

import argparse
import json

from api.storage import SchedulerStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview scheduler routing for a node")
    parser.add_argument("--node-id", required=True)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    store = SchedulerStore()
    preview = store.queued_route_preview(args.node_id, limit=args.limit)
    print(json.dumps(preview, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
