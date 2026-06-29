from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.testnet_v0 import run_testnet_v0_check


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local Testnet v0 readiness checklist")
    parser.add_argument("--work-dir", default=None)
    args = parser.parse_args()
    result = run_testnet_v0_check(args.work_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
