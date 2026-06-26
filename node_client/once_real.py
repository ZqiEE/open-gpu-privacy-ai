from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

from node_client.client import heartbeat, register_node, request_with_retry, setup_logging
from node_client.client_real import RealNodeConfig, limits
from node_client.real_runner import JobRunner
from node_client.resource_guard import ResourceGuard
from node_client.task_policy import TaskPolicy


def fetch_job(config: RealNodeConfig, node_id: str) -> dict | None:
    response = request_with_retry("GET", f"{config.api_url}/jobs/next", params={"node_id": node_id})
    return response.json().get("job")


def submit_result(config: RealNodeConfig, node_id: str, result: dict) -> None:
    request_with_retry("POST", f"{config.api_url}/jobs/result", json=result | {"node_id": node_id})


def run_once(config: RealNodeConfig) -> dict:
    setup_logging(config.log_dir)
    node_id = register_node(config)  # type: ignore[arg-type]
    guard = ResourceGuard(limits(config))
    ok, reason = guard.can_run_job()
    if not ok:
        heartbeat(config, node_id, "idle")  # type: ignore[arg-type]
        return {"ok": False, "node_id": node_id, "reason": reason}
    job = fetch_job(config, node_id)
    if not job:
        heartbeat(config, node_id, "idle")  # type: ignore[arg-type]
        return {"ok": False, "node_id": node_id, "reason": "no job"}
    heartbeat(config, node_id, "busy")  # type: ignore[arg-type]
    runner = JobRunner(TaskPolicy.default().__class__(TaskPolicy.default().allowed_job_types, config.max_payload_bytes, config.max_runtime_seconds))
    result = asdict(runner.run(job))
    submit_result(config, node_id, result)
    heartbeat(config, node_id, "idle")  # type: ignore[arg-type]
    return {"ok": result["status"] == "ok", "node_id": node_id, "job_id": result["job_id"], "status": result["status"], "summary": result["output_summary"]}


def main() -> None:
    p = argparse.ArgumentParser(description="Run one real Ailovanta node job")
    p.add_argument("--api-url", default="http://127.0.0.1:8000")
    p.add_argument("--contribution", type=int, default=30)
    p.add_argument("--max-cpu-percent", type=int, default=95)
    p.add_argument("--min-free-memory-gb", type=float, default=0.2)
    p.add_argument("--max-gpu-percent", type=int, default=95)
    p.add_argument("--max-gpu-memory-percent", type=int, default=95)
    p.add_argument("--max-gpu-temperature-c", type=int, default=85)
    p.add_argument("--min-idle-seconds", type=int, default=0)
    p.add_argument("--allow-on-battery", action="store_true")
    p.add_argument("--log-dir", default="runtime_data/logs")
    p.add_argument("--identity-path", default="runtime_data/node_identity.json")
    p.add_argument("--max-payload-bytes", type=int, default=65536)
    p.add_argument("--max-runtime-seconds", type=float, default=120.0)
    args = p.parse_args()
    cfg = RealNodeConfig(args.api_url.rstrip("/"), args.contribution, 1, args.max_cpu_percent, args.min_free_memory_gb, Path(args.log_dir), Path(args.identity_path), args.max_payload_bytes, args.max_runtime_seconds, args.max_gpu_percent, args.max_gpu_memory_percent, args.max_gpu_temperature_c, args.min_idle_seconds, not args.allow_on_battery)
    print(run_once(cfg))


if __name__ == "__main__":
    main()
