from __future__ import annotations

import argparse
import json

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute latest rollback action")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    with httpx.Client(timeout=120) as client:
        response = client.post(args.api_url.rstrip("/") + "/rollback/latest")
        response.raise_for_status()
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
