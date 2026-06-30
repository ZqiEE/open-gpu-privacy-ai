from __future__ import annotations

import argparse
import json

from api.route_health import RouteHealth


def main() -> int:
    parser = argparse.ArgumentParser(description="Check active route health")
    parser.add_argument("--route-key", default="owned-chat/default")
    parser.add_argument("--disable-if-bad", action="store_true")
    parser.add_argument("--verify-artifact", action="store_true")
    parser.add_argument("--verify-distribution", action="store_true")
    parser.add_argument("--verify-chain", action="store_true")
    args = parser.parse_args()
    checker = RouteHealth()
    data = (
        checker.disable_if_bad(args.route_key, verify_artifact=args.verify_artifact, verify_distribution=args.verify_distribution, verify_chain=args.verify_chain)
        if args.disable_if_bad
        else checker.check(args.route_key, verify_artifact=args.verify_artifact, verify_distribution=args.verify_distribution, verify_chain=args.verify_chain)
    )
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0 if data.get("ok") or data.get("changed") is False else 1


if __name__ == "__main__":
    raise SystemExit(main())
