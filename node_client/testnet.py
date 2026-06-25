from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import httpx

from node_client.cap import detect
from node_client.client import NodeConfig, register_node
from node_client.identity import NodeIdentity


def post(api_url: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = httpx.post(api_url.rstrip("/") + path, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


def register_runtime(api_url: str, node_id: str, region: str, engines: list[str], cached_models: list[str], cached_adapters: list[str], trust: float) -> dict[str, Any]:
    cap = detect(region=region, engines=engines, cached_models=cached_models, cached_adapters=cached_adapters)
    runtime_id = "rt-" + node_id
    payload = cap.runtime(runtime_id=runtime_id, node_id=node_id, trust=trust)
    result = post(api_url, "/runtime/nodes/register", payload)
    return {"capability": cap.to_dict(), "runtime": result}


def bootstrap(args: argparse.Namespace) -> dict[str, Any]:
    cfg = NodeConfig(
        api_url=args.api_url.rstrip("/"),
        contribution_percent=args.contribution,
        poll_seconds=args.poll_seconds,
        max_cpu_percent=args.max_cpu_percent,
        min_free_memory_gb=args.min_free_memory_gb,
        log_dir=Path(args.log_dir),
        identity_path=Path(args.identity_path),
        max_payload_bytes=args.max_payload_bytes,
        max_runtime_seconds=args.max_runtime_seconds,
    )
    node_id = register_node(cfg)
    runtime = register_runtime(args.api_url.rstrip("/"), node_id, args.region, args.engine, args.cached_model, args.cached_adapter, args.trust)
    NodeIdentity(Path(args.identity_path)).set(node_id)
    return {"ok": True, "node_id": node_id, "runtime": runtime}


def main() -> int:
    parser = argparse.ArgumentParser(description="Ailovanta node testnet bootstrap")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--contribution", type=int, default=30)
    parser.add_argument("--poll-seconds", type=int, default=5)
    parser.add_argument("--max-cpu-percent", type=int, default=70)
    parser.add_argument("--min-free-memory-gb", type=float, default=1.5)
    parser.add_argument("--log-dir", default="runtime_data/logs")
    parser.add_argument("--identity-path", default="runtime_data/node_identity.json")
    parser.add_argument("--max-payload-bytes", type=int, default=16384)
    parser.add_argument("--max-runtime-seconds", type=float, default=10.0)
    parser.add_argument("--region", default="global")
    parser.add_argument("--engine", action="append", default=["python", "local"])
    parser.add_argument("--cached-model", action="append", default=[])
    parser.add_argument("--cached-adapter", action="append", default=[])
    parser.add_argument("--trust", type=float, default=0.5)
    args = parser.parse_args()
    print(json.dumps(bootstrap(args), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
