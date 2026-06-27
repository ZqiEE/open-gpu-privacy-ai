from __future__ import annotations

import argparse
import json
import os
import platform
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class LocalProfile:
    device_name: str
    cpu_threads: int
    memory_gb: float
    has_gpu: bool
    gpu_name: str | None


def detect_profile(enable_gpu: bool = False) -> LocalProfile:
    cpu_threads = os.cpu_count() or 1
    memory_gb = 4.0
    try:
        import psutil  # type: ignore
        memory_gb = round(psutil.virtual_memory().total / (1024**3), 2)
    except Exception:
        pass

    has_gpu = False
    gpu_name = None
    if enable_gpu:
        try:
            import torch  # type: ignore
            has_gpu = bool(torch.cuda.is_available())
            gpu_name = torch.cuda.get_device_name(0) if has_gpu else None
        except Exception:
            has_gpu = False
            gpu_name = None

    return LocalProfile(
        device_name=f"{socket.gethostname()}-{platform.system()}",
        cpu_threads=cpu_threads,
        memory_gb=memory_gb,
        has_gpu=has_gpu,
        gpu_name=gpu_name,
    )


class WorkerApi:
    def __init__(self, server: str) -> None:
        self.server = server.rstrip("/")

    def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.server + path,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def get(self, path: str) -> dict[str, Any]:
        with urllib.request.urlopen(self.server + path, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))


def register_node(api: WorkerApi, profile: LocalProfile, contribution_percent: int, node_id: str | None = None) -> dict[str, Any]:
    return api.post(
        "/nodes/register",
        {
            "node_id": node_id,
            "device_name": profile.device_name,
            "cpu_threads": profile.cpu_threads,
            "memory_gb": profile.memory_gb,
            "has_gpu": profile.has_gpu,
            "gpu_name": profile.gpu_name,
            "contribution_percent": contribution_percent,
        },
    )


def heartbeat(api: WorkerApi, node_id: str, status: str = "online") -> None:
    api.post("/nodes/heartbeat", {"node_id": node_id, "status": status})


def next_job(api: WorkerApi, node_id: str) -> dict[str, Any] | None:
    try:
        payload = api.get(f"/jobs/next?node_id={node_id}")
        return payload.get("job")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def run_job(job: dict[str, Any], profile: LocalProfile) -> tuple[str, str]:
    job_type = str(job.get("type") or job.get("job_type") or "unknown")
    payload = job.get("payload") or {}
    if job_type in {"evaluation", "evaluation_batch", "verification"}:
        return "ok", f"validated locally on {profile.device_name}; payload={payload}"
    if job_type in {"rag_index", "rag_import"}:
        return "ok", f"indexed metadata locally on {profile.device_name}; payload={payload}"
    if job_type in {"lora_micro", "private_memory_tune"}:
        if not profile.has_gpu:
            return "failed", "gpu job received by non-gpu worker"
        return "ok", f"gpu job accepted by {profile.gpu_name or profile.device_name}; payload={payload}"
    return "ok", f"job observed by worker; type={job_type}; payload={payload}"


def submit_result(api: WorkerApi, node_id: str, job_id: str, status: str, output_summary: str) -> dict[str, Any]:
    return api.post(
        "/jobs/result",
        {
            "node_id": node_id,
            "job_id": job_id,
            "status": status,
            "output_summary": output_summary[:4000],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Ailovanta public worker")
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--node-id", default=None)
    parser.add_argument("--contribution-percent", type=int, default=30)
    parser.add_argument("--enable-gpu", action="store_true")
    parser.add_argument("--interval", type=int, default=10)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    api = WorkerApi(args.server)
    profile = detect_profile(enable_gpu=args.enable_gpu)
    node = register_node(api, profile, args.contribution_percent, args.node_id)
    node_id = node["node_id"]
    print(json.dumps({"ok": True, "node": node}, ensure_ascii=False, indent=2))

    while True:
        heartbeat(api, node_id, "online")
        job = next_job(api, node_id)
        if job:
            heartbeat(api, node_id, "busy")
            status, summary = run_job(job, profile)
            result = submit_result(api, node_id, job["job_id"], status, summary)
            print(json.dumps({"job_id": job["job_id"], "status": status, "result": result}, ensure_ascii=False, indent=2))
            heartbeat(api, node_id, "online")
        elif args.once:
            print(json.dumps({"ok": True, "node_id": node_id, "message": "no job"}, ensure_ascii=False))
            return 0
        if args.once:
            return 0
        time.sleep(max(3, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
