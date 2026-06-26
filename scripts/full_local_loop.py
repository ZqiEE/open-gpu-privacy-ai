from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import httpx


def main() -> int:
    p = argparse.ArgumentParser(description="Run local Ailovanta shard build loop")
    p.add_argument("--api-url", default="http://127.0.0.1:8000")
    p.add_argument("--data-file", required=True)
    p.add_argument("--total-tokens", type=int, default=256)
    p.add_argument("--shard-tokens", type=int, default=64)
    p.add_argument("--model-id", default="ailovanta-foundation")
    p.add_argument("--version", default="v0.1")
    p.add_argument("--max-runtime-seconds", type=float, default=120.0)
    p.add_argument("--node-runs", type=int, default=4)
    args = p.parse_args()

    data_path = Path(args.data_file).resolve()
    if not data_path.exists():
        raise SystemExit("data file not found: " + str(data_path))

    plan_resp = httpx.post(
        args.api_url.rstrip("/") + "/swarm-model/plans",
        json={
            "model_id": args.model_id,
            "target_version": args.version,
            "dataset_uri": "file://" + str(data_path),
            "total_tokens": args.total_tokens,
            "shard_tokens": args.shard_tokens,
            "min_gpu_memory_gb": 0,
            "enqueue": True,
        },
        timeout=30,
    )
    plan_resp.raise_for_status()
    plan_data = plan_resp.json()
    plan_id = plan_data["plan"]["plan_id"]
    print(json.dumps({"created_plan": plan_id, "job_count": plan_data.get("job_count")}, ensure_ascii=False, indent=2))

    for index in range(args.node_runs):
        proc = subprocess.run(
            [sys.executable, "-m", "node_client.once_real", "--api-url", args.api_url, "--max-runtime-seconds", str(args.max_runtime_seconds), "--max-payload-bytes", "65536", "--allow-on-battery"],
            check=False,
        )
        print(json.dumps({"one_shot_node_run": index + 1, "returncode": proc.returncode}, ensure_ascii=False))
        if proc.returncode != 0:
            return proc.returncode

    index_proc = subprocess.run([sys.executable, "scripts/didx.py", "--scan", "--plan-id", plan_id, "--award"], check=False)
    if index_proc.returncode != 0:
        return index_proc.returncode
    build = subprocess.run([sys.executable, "scripts/mck.py", "--plan-id", plan_id, "--model-id", args.model_id, "--version", args.version], check=False)
    print(json.dumps({"plan_id": plan_id, "build_returncode": build.returncode}, ensure_ascii=False, indent=2))
    return build.returncode


if __name__ == "__main__":
    raise SystemExit(main())
