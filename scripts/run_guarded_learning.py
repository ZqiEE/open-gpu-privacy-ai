from __future__ import annotations

import argparse
import json

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AutoTruth learning with eval gate before runtime import")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--core-path", default="../ailovanta-core")
    parser.add_argument("--baseline-score", type=float, default=0.45)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--allow-shadow-import", action="store_true")
    args = parser.parse_args()
    payload = {
        "core_path": args.core_path,
        "baseline_score": args.baseline_score,
        "max_steps": args.max_steps,
        "allow_shadow_import": args.allow_shadow_import,
    }
    with httpx.Client(timeout=600) as client:
        response = client.post(args.api_url.rstrip("/") + "/learning/gate/run", json=payload)
        response.raise_for_status()
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
