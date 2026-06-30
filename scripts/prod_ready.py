from __future__ import annotations

import argparse
import json

from api.prod_ready import check_production_ready


def main() -> int:
    parser = argparse.ArgumentParser(description="Check production readiness")
    parser.add_argument("--result", default=None)
    parser.add_argument("--route-key", default="owned-chat/default")
    parser.add_argument("--verify-bytes", action="store_true")
    parser.add_argument("--verify-distribution", action="store_true")
    parser.add_argument("--verify-chain", action="store_true")
    args = parser.parse_args()
    data = check_production_ready(result_path=args.result, route_key=args.route_key, verify_bytes=args.verify_bytes, verify_distribution=args.verify_distribution, verify_chain=args.verify_chain)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0 if data.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
