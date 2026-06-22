from __future__ import annotations

import argparse

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test Open GPU Privacy AI API")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    api = args.api_url.rstrip("/")

    with httpx.Client(timeout=10) as client:
        root = client.get(f"{api}/")
        root.raise_for_status()
        print("root:", root.json())

        node = client.post(
            f"{api}/nodes/register",
            json={
                "device_name": "smoke-node",
                "cpu_threads": 4,
                "memory_gb": 8,
                "has_gpu": False,
                "gpu_name": None,
                "contribution_percent": 30,
            },
        )
        node.raise_for_status()
        node_id = node.json()["node_id"]
        print("node_id:", node_id)

        job = client.get(f"{api}/jobs/next", params={"node_id": node_id})
        job.raise_for_status()
        payload = job.json().get("job")
        print("job:", payload)

        if payload:
            result = client.post(
                f"{api}/jobs/result",
                json={
                    "node_id": node_id,
                    "job_id": payload["id"],
                    "status": "ok",
                    "output_summary": "simulated smoke test result",
                },
            )
            result.raise_for_status()
            print("result:", result.json())

        status = client.get(f"{api}/network/status")
        status.raise_for_status()
        print("status:", status.json())


if __name__ == "__main__":
    main()
