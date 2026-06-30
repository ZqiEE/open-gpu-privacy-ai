from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.release_gate import release_gate


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Ailovanta release check")
    parser.add_argument("--core-path", default="../ailovanta-core")
    parser.add_argument("--result", default=None)
    parser.add_argument("--route-key", default="owned-chat/default")
    parser.add_argument("--run-tests", action="store_true")
    parser.add_argument("--verify-bytes", action="store_true")
    parser.add_argument("--verify-distribution", action="store_true")
    parser.add_argument("--verify-chain", action="store_true")
    args = parser.parse_args()
    data = release_gate(core_path=args.core_path, result_path=args.result, route_key=args.route_key, run_tests=args.run_tests, verify_bytes=args.verify_bytes, verify_distribution=args.verify_distribution, verify_chain=args.verify_chain)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0 if data.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
