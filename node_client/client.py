from __future__ import annotations

import argparse
import platform
import time
from dataclasses import dataclass

import httpx
import psutil


@dataclass
class NodeConfig:
    api_url: str
    contribution_percent: int
    poll_seconds: int


def detect_device() -> dict:
    return {
        "device_name": platform.node() or "local-node",
        "cpu_threads": psutil.cpu_count(logical=True) or 1,
        "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "has_gpu": False,
        "gpu_name": None,
    }


def register_node(client: httpx.Client, config: NodeConfig) -> str:
    payload = detect_device() | {"contribution_percent": config.contribution_percent}
    response = client.post(f"{config.api_url}/nodes/register", json=payload)
    response.raise_for_status()
    data = response.json()
    node_id = data["node_id"]
    print(f"registered node: {node_id} score={data.get('score')}")
    return node_id


def heartbeat(client: httpx.Client, config: NodeConfig, node_id: str, status: str = "online") -> None:
    response = client.post(f"{config.api_url}/nodes/heartbeat", json={"node_id": node_id, "status": status})
    response.raise_for_status()


def run_job(job: dict) -> dict:
    job_type = job.get("type", "unknown")
    print(f"running job {job.get('id')} type={job_type}")
    time.sleep(1)
    return {
        "job_id": job["id"],
        "status": "ok",
        "output_summary": f"simulated result for {job_type}",
    }


def worker_loop(config: NodeConfig) -> None:
    with httpx.Client(timeout=10) as client:
        node_id = register_node(client, config)
        while True:
            heartbeat(client, config, node_id, "online")
            response = client.get(f"{config.api_url}/jobs/next", params={"node_id": node_id})
            response.raise_for_status()
            payload = response.json()
            job = payload.get("job")
            if not job:
                print("no job; waiting")
                time.sleep(config.poll_seconds)
                continue
            heartbeat(client, config, node_id, "busy")
            result = run_job(job) | {"node_id": node_id}
            submit = client.post(f"{config.api_url}/jobs/result", json=result)
            submit.raise_for_status()
            heartbeat(client, config, node_id, "idle")


def main() -> None:
    parser = argparse.ArgumentParser(description="Open GPU Privacy AI local node client")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--contribution", type=int, default=30)
    parser.add_argument("--poll-seconds", type=int, default=5)
    args = parser.parse_args()
    worker_loop(NodeConfig(args.api_url.rstrip("/"), args.contribution, args.poll_seconds))


if __name__ == "__main__":
    main()
