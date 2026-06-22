from __future__ import annotations

import argparse
import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import httpx

from node_client.device import detect_device
from node_client.identity import NodeIdentity
from node_client.job_runner import JobRunner
from node_client.resource_guard import ResourceGuard, ResourceLimits
from node_client.task_policy import TaskPolicy


@dataclass
class NodeConfig:
    api_url: str
    contribution_percent: int
    poll_seconds: int
    max_cpu_percent: int
    min_free_memory_gb: float
    log_dir: Path
    identity_path: Path
    max_payload_bytes: int
    max_runtime_seconds: float


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_dir / "node.log", encoding="utf-8")],
    )


def request_with_retry(method: str, url: str, *, attempts: int = 3, **kwargs) -> httpx.Response:
    last_error: Exception | None = None
    for index in range(attempts):
        try:
            response = httpx.request(method, url, timeout=10, **kwargs)
            response.raise_for_status()
            return response
        except Exception as exc:
            last_error = exc
            sleep_for = min(2**index, 8)
            logging.warning("request failed attempt=%s url=%s error=%s", index + 1, url, exc)
            time.sleep(sleep_for)
    raise RuntimeError(f"request failed after {attempts} attempts: {url}") from last_error


def register_node(config: NodeConfig) -> str:
    identity = NodeIdentity(config.identity_path)
    local_node_id = identity.get_or_create()
    profile = detect_device()
    payload = profile.to_api_payload(config.contribution_percent) | {"node_id": local_node_id}
    response = request_with_retry("POST", f"{config.api_url}/nodes/register", json=payload)
    data = response.json()
    node_id = data["node_id"]
    identity.set(node_id)
    logging.info("registered node=%s score=%s gpu=%s", node_id, data.get("score"), payload.get("gpu_name"))
    return node_id


def heartbeat(config: NodeConfig, node_id: str, status: str = "online") -> None:
    request_with_retry("POST", f"{config.api_url}/nodes/heartbeat", json={"node_id": node_id, "status": status})


def fetch_job(config: NodeConfig, node_id: str) -> dict | None:
    response = request_with_retry("GET", f"{config.api_url}/jobs/next", params={"node_id": node_id})
    return response.json().get("job")


def submit_result(config: NodeConfig, node_id: str, result: dict) -> None:
    payload = result | {"node_id": node_id}
    request_with_retry("POST", f"{config.api_url}/jobs/result", json=payload)


def worker_loop(config: NodeConfig) -> None:
    setup_logging(config.log_dir)
    guard = ResourceGuard(ResourceLimits(config.max_cpu_percent, config.min_free_memory_gb))
    runner = JobRunner(TaskPolicy.default().__class__(TaskPolicy.default().allowed_job_types, config.max_payload_bytes, config.max_runtime_seconds))
    node_id = register_node(config)
    while True:
        try:
            heartbeat(config, node_id, "online")
            allowed, reason = guard.can_run_job()
            if not allowed:
                logging.info("resource guard paused node: %s", reason)
                time.sleep(config.poll_seconds)
                continue
            job = fetch_job(config, node_id)
            if not job:
                logging.info("no job; waiting")
                time.sleep(config.poll_seconds)
                continue
            heartbeat(config, node_id, "busy")
            logging.info("running job id=%s type=%s", job.get("id"), job.get("type"))
            result = asdict(runner.run(job))
            submit_result(config, node_id, result)
            heartbeat(config, node_id, "idle")
            logging.info("submitted job id=%s status=%s reason=%s", result["job_id"], result["status"], result.get("policy_reason"))
        except KeyboardInterrupt:
            logging.info("node stopped by user")
            heartbeat(config, node_id, "offline")
            raise
        except Exception as exc:
            logging.exception("worker loop error: %s", exc)
            time.sleep(config.poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Open GPU Privacy AI hardened local node client")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--contribution", type=int, default=30)
    parser.add_argument("--poll-seconds", type=int, default=5)
    parser.add_argument("--max-cpu-percent", type=int, default=70)
    parser.add_argument("--min-free-memory-gb", type=float, default=1.5)
    parser.add_argument("--log-dir", default="runtime_data/logs")
    parser.add_argument("--identity-path", default="runtime_data/node_identity.json")
    parser.add_argument("--max-payload-bytes", type=int, default=16384)
    parser.add_argument("--max-runtime-seconds", type=float, default=10.0)
    args = parser.parse_args()
    worker_loop(
        NodeConfig(
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
    )


if __name__ == "__main__":
    main()
