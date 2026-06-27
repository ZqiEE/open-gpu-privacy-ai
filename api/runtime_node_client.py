from __future__ import annotations

import argparse
import json
import os
import platform
import socket
import time
import urllib.request
from pathlib import Path
from typing import Any


def post(server: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        server.rstrip("/") + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def scan_manifests(path: str | Path) -> list[str]:
    root = Path(path)
    if not root.exists():
        return []
    models: list[str] = []
    for item in root.glob("*.json"):
        try:
            data = json.loads(item.read_text(encoding="utf-8"))
            name = data.get("name")
            version = data.get("version")
            if name and version:
                models.append(f"{name}:{version}")
        except Exception:
            pass
    return sorted(set(models))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--server", default="http://127.0.0.1:8000")
    p.add_argument("--runtime-id", default=None)
    p.add_argument("--node-id", default=None)
    p.add_argument("--pool", default="small_gpu_pool")
    p.add_argument("--region", default="global")
    p.add_argument("--gpu-memory-gb", type=float, default=0.0)
    p.add_argument("--available-gpu-memory-gb", type=float, default=0.0)
    p.add_argument("--trust-score", type=float, default=0.7)
    p.add_argument("--current-load", type=float, default=0.0)
    p.add_argument("--price-per-1k-tokens", type=float, default=0.0)
    p.add_argument("--latency-ms", type=int, default=800)
    p.add_argument("--manifest-dir", default="runtime_data/manifests")
    p.add_argument("--interval", type=int, default=20)
    p.add_argument("--once", action="store_true")
    args = p.parse_args()

    host = f"{socket.gethostname()}-{platform.system()}"
    runtime_id = args.runtime_id or f"runtime-{host}"
    node_id = args.node_id or f"node-{host}"

    while True:
        cached = scan_manifests(args.manifest_dir)
        body = {
            "runtime_id": runtime_id,
            "node_id": node_id,
            "pool": args.pool,
            "region": args.region,
            "status": "online",
            "gpu_memory_gb": args.gpu_memory_gb,
            "available_gpu_memory_gb": args.available_gpu_memory_gb,
            "trust_score": args.trust_score,
            "current_load": args.current_load,
            "price_per_1k_tokens": args.price_per_1k_tokens,
            "latency_ms": args.latency_ms,
            "supported_engines": ["manifest"],
            "cached_models": cached,
            "cached_adapters": cached,
        }
        result = post(args.server, "/runtime/nodes/register", body)
        print(json.dumps({"ok": True, "runtime": result, "cached_models": cached}, ensure_ascii=False, indent=2))
        if args.once:
            return 0
        time.sleep(max(5, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
