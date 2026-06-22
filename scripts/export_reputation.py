from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Export node reputation leaderboard")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", default="runtime_data/reputation_leaderboard.json")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    api = args.api_url.rstrip("/")

    with httpx.Client(timeout=10) as client:
        response = client.get(f"{api}/reputation/leaderboard", params={"limit": args.limit})
        response.raise_for_status()
        data = response.json()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
