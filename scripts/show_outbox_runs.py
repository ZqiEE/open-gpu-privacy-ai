from __future__ import annotations

import argparse
import json

from api.outbox_run import list_runs


def main() -> int:
    parser = argparse.ArgumentParser(description="Show recent outbox run records")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    items = list_runs(limit=args.limit)
    print(json.dumps({"ok": True, "count": len(items), "items": items}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
