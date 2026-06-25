from __future__ import annotations

import argparse
import json

import httpx


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--api-url", default="http://127.0.0.1:8000")
    a = p.parse_args()
    with httpx.Client(timeout=30) as client:
        r = client.get(a.api_url.rstrip("/") + "/parcels/pending")
        r.raise_for_status()
        print(json.dumps(r.json(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
