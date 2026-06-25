from __future__ import annotations

import argparse
import json

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="Create and run a foundation job from latest learning pack")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--core-path", default="../ailovanta-core")
    parser.add_argument("--model-id", default="ailovanta-owned")
    parser.add_argument("--target-version", default="candidate")
    parser.add_argument("--max-steps", type=int, default=100)
    args = parser.parse_args()
    payload = {
        "model_id": args.model_id,
        "target_version": args.target_version,
        "max_steps": args.max_steps,
        "core_path": args.core_path,
    }
    with httpx.Client(timeout=300) as client:
        response = client.post(args.api_url.rstrip("/") + "/learning/foundation/run", json=payload)
        response.raise_for_status()
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
