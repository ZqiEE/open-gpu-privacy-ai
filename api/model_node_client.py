from __future__ import annotations

import argparse
import json
import platform
import socket
import urllib.request
from typing import Any


def get(server: str, path: str) -> dict[str, Any]:
    with urllib.request.urlopen(server.rstrip("/") + path, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def post(server: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(server.rstrip("/") + path, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--server", default="http://127.0.0.1:8000")
    p.add_argument("--pool", default="small_gpu_pool")
    p.add_argument("--gpu-memory-gb", type=float, default=0.0)
    p.add_argument("--available-gpu-memory-gb", type=float, default=0.0)
    args = p.parse_args()

    items = get(args.server, "/catalog/items?status=published").get("items", [])
    keys = sorted({f"{item['name']}:{item['version']}" for item in items if item.get("name") and item.get("version")})
    host = f"{socket.gethostname()}-{platform.system()}"
    body = {
        "runtime_id": f"runtime-{host}",
        "node_id": f"node-{host}",
        "pool": args.pool,
        "region": "global",
        "status": "online",
        "gpu_memory_gb": args.gpu_memory_gb,
        "available_gpu_memory_gb": args.available_gpu_memory_gb,
        "trust_score": 0.7,
        "current_load": 0.0,
        "price_per_1k_tokens": 0.0,
        "latency_ms": 800,
        "supported_engines": ["manifest"],
        "cached_models": keys,
        "cached_adapters": keys,
    }
    print(json.dumps(post(args.server, "/runtime/nodes/register", body), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
