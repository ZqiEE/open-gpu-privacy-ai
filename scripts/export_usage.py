from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Export local usage events")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--user-id", default="local")
    parser.add_argument("--output", default="runtime_data/usage_export.json")
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()
    api = args.api_url.rstrip("/")

    with httpx.Client(timeout=10) as client:
        summary = client.get(f"{api}/usage/summary", params={"user_id": args.user_id})
        summary.raise_for_status()
        events = client.get(f"{api}/usage/events", params={"user_id": args.user_id, "limit": args.limit})
        events.raise_for_status()

    data = {"summary": summary.json(), "events": events.json()["events"]}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
