from __future__ import annotations

import argparse
import json

from api.route_book import RouteBook


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage active route book")
    parser.add_argument("action", choices=["list", "get", "set", "disable"])
    parser.add_argument("--route-key", default="owned-chat/default")
    parser.add_argument("--model-key", default=None)
    parser.add_argument("--binding-id", default=None)
    parser.add_argument("--reason", default=None)
    args = parser.parse_args()
    store = RouteBook()
    if args.action == "list":
        out = {"items": store.list_routes()}
    elif args.action == "get":
        out = store.get(args.route_key)
    elif args.action == "set":
        if not args.model_key:
            raise SystemExit("--model-key required")
        out = store.set_active(args.route_key, args.model_key, binding_id=args.binding_id, reason=args.reason)
    else:
        out = store.disable(args.route_key, reason=args.reason)
    print(json.dumps({"ok": out is not None, "result": out}, ensure_ascii=False, indent=2))
    return 0 if out is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
