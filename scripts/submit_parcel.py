from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("payload_path")
    p.add_argument("--api-url", default="http://127.0.0.1:8000")
    a = p.parse_args()
    payload = json.loads(Path(a.payload_path).read_text(encoding="utf-8"))
    if "id" not in payload and "receipt_id" in payload:
        payload = {"id": payload["receipt_id"], "source": payload}
    with httpx.Client(timeout=30) as client:
        r = client.post(a.api_url.rstrip("/") + "/parcels/submit", json={"payload": payload})
        r.raise_for_status()
        print(json.dumps(r.json(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
