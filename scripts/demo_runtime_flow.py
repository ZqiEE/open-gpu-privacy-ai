from __future__ import annotations

import argparse

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a minimal Ailovanta runtime demo")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    api = args.api_url.rstrip("/")

    with httpx.Client(timeout=10) as client:
        model = client.post(
            f"{api}/runtime/models/register",
            json={"model_id": "demo-model", "version": "1", "manifest_hash": "sha256:demo"},
        )
        model.raise_for_status()
        print("model:", model.json())

        node = client.post(
            f"{api}/runtime/nodes/register",
            json={
                "runtime_id": "demo-runtime",
                "node_id": "demo-node",
                "pool": "small_gpu_pool",
                "available_gpu_memory_gb": 8,
                "cached_models": ["demo-model:1"],
            },
        )
        node.raise_for_status()
        print("runtime:", node.json())

        routed = client.post(
            f"{api}/runtime/route",
            json={"request_id": "demo-request", "model_id": "demo-model", "version": "1"},
        )
        routed.raise_for_status()
        print("route:", routed.json())

        status = client.get(f"{api}/runtime/status")
        status.raise_for_status()
        print("status:", status.json())

        history = client.get(f"{api}/runtime/assignments")
        history.raise_for_status()
        print("history:", history.json())


if __name__ == "__main__":
    main()
