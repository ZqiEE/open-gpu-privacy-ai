from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.credit import award_verified_items, load_ledger
from api.didx import load, save, scan


def main() -> int:
    p = argparse.ArgumentParser(description="Inspect model delta index")
    p.add_argument("--scan", action="store_true")
    p.add_argument("--plan-id")
    p.add_argument("--all", action="store_true")
    p.add_argument("--award", action="store_true")
    args = p.parse_args()
    data = save(scan()) if args.scan else load()
    items = data.get("items", [])
    if args.plan_id:
        items = [item for item in items if item.get("plan_id") == args.plan_id]
    if not args.all:
        items = [item for item in items if item.get("hash_ok")]
    ledger = award_verified_items(items) if args.award else load_ledger()
    print(json.dumps({"count": len(items), "items": items, "credits": ledger.get("nodes", {})}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
