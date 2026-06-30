from __future__ import annotations

import argparse
import json
import os
import platform
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from api.candidate_failure_actions import mark_action_submitted
from api.gpu_probe import detect_gpu
from api.model_job import run_model_job
from api.training_artifact_binding import bind_local_training_artifact


def auth_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("AILOVANTA_NODE_TOKEN")
    if token:
        headers["X-Ailovanta-Node-Token"] = token
    return headers


def post(server: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        server.rstrip("/") + path,
        data=data,
        headers=auth_headers(),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def get(server: str, path: str) -> dict[str, Any]:
    req = urllib.request.Request(server.rstrip("/") + path, headers=auth_headers(), method="GET")
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def try_post(server: str, path: str, body: dict[str, Any]) -> dict[str, Any] | None:
    try:
        return post(server, path, body)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def submit_failure_actions(server: str, binding: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not binding:
        return []
    metadata = binding.get("metadata") if isinstance(binding.get("metadata"), dict) else {}
    failure_actions = metadata.get("failure_actions") if isinstance(metadata.get("failure_actions"), dict) else {}
    submitted: list[dict[str, Any]] = []
    for action in failure_actions.get("actions", []) or []:
        if action.get("action_type") != "training_retrain" or action.get("status") != "queued":
            continue
        request = action.get("training_job_request") if isinstance(action.get("training_job_request"), dict) else {}
        if not request.get("dataset_uri"):
            continue
        response = post(server, "/training/jobs", request)
        marked = mark_action_submitted(str(action.get("action_id")), response)
        submitted.append({"action_id": action.get("action_id"), "response": response, "marked": marked})
    return submitted


def connection_unavailable(exc: Exception) -> bool:
    return isinstance(exc, urllib.error.URLError)


def detect(enable_gpu: bool) -> dict[str, Any]:
    memory_gb = 4.0
    try:
        import psutil  # type: ignore
        memory_gb = round(psutil.virtual_memory().total / (1024**3), 2)
    except Exception:
        pass

    has_gpu = False
    gpu_name = None
    if enable_gpu:
        gpu = detect_gpu()
        has_gpu = bool(gpu.get("has_gpu"))
        gpu_name = gpu.get("gpu_name")

    return {
        "device_name": f"{socket.gethostname()}-{platform.system()}",
        "cpu_threads": os.cpu_count() or 1,
        "memory_gb": memory_gb,
        "has_gpu": has_gpu,
        "gpu_name": gpu_name,
    }


def make_output(job: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    payload = job.get("payload") or {}
    job_id = job.get("job_id") or job.get("id") or "manual"
    return run_model_job(payload, profile, job_id)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--server", default="http://127.0.0.1:8000")
    p.add_argument("--node-id", default=None)
    p.add_argument("--contribution-percent", type=int, default=30)
    p.add_argument("--enable-gpu", action="store_true")
    p.add_argument("--interval", type=int, default=10)
    p.add_argument("--once", action="store_true")
    args = p.parse_args()

    profile = detect(args.enable_gpu)
    node = post(args.server, "/nodes/register", {**profile, "node_id": args.node_id, "contribution_percent": args.contribution_percent})
    node_id = node["node_id"]
    print(json.dumps({"ok": True, "node": node}, ensure_ascii=False, indent=2))

    while True:
        try:
            post(args.server, "/nodes/heartbeat", {"node_id": node_id, "status": "online"})
        except Exception as exc:
            if connection_unavailable(exc):
                print(json.dumps({"ok": False, "reason": "server_unavailable", "server": args.server, "message": str(exc)}, ensure_ascii=False))
                if args.once:
                    return 0
                time.sleep(max(3, args.interval))
                continue
            raise
        try:
            job = get(args.server, f"/jobs/next?node_id={node_id}").get("job")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                job = None
            else:
                raise
        except Exception as exc:
            if connection_unavailable(exc):
                print(json.dumps({"ok": False, "reason": "server_unavailable", "server": args.server, "message": str(exc)}, ensure_ascii=False))
                if args.once:
                    return 0
                time.sleep(max(3, args.interval))
                continue
            raise

        if job:
            post(args.server, "/nodes/heartbeat", {"node_id": node_id, "status": "busy"})
            job_id = job.get("job_id") or job.get("id")
            output = make_output(job, profile)
            if output.get("status") == "failed":
                summary = f"node failed task on {profile['device_name']}; reason={output.get('notes')}"
                result = post(args.server, "/jobs/result", {"node_id": node_id, "job_id": job_id, "status": "failed", "output_summary": summary})
                print(json.dumps({"job_id": job_id, "result": result, "training_output": output}, ensure_ascii=False, indent=2))
                post(args.server, "/nodes/heartbeat", {"node_id": node_id, "status": "online"})
                if args.once:
                    return 0
                time.sleep(max(3, args.interval))
                continue
            catalog_result = None
            if (job.get("payload") or {}).get("catalog", True):
                catalog_result = try_post(args.server, "/catalog/items", output)
            summary = f"node finished task on {profile['device_name']}; output={output['location']}"
            result = post(args.server, "/jobs/result", {"node_id": node_id, "job_id": job_id, "status": "ok", "output_summary": summary})
            binding = bind_local_training_artifact(output)
            failure_action_submissions = submit_failure_actions(args.server, binding)
            print(json.dumps({"job_id": job_id, "result": result, "catalog": catalog_result, "runtime_binding": binding, "failure_action_submissions": failure_action_submissions}, ensure_ascii=False, indent=2))
            post(args.server, "/nodes/heartbeat", {"node_id": node_id, "status": "online"})
        elif args.once:
            print(json.dumps({"ok": True, "node_id": node_id, "message": "no job"}, ensure_ascii=False))
            return 0

        if args.once:
            return 0
        time.sleep(max(3, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
