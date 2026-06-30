from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def post(server: str, path: str, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        server.rstrip("/") + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def write_seed_dataset(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {"text": "Ailovanta trains from authorized source data into verified code tasks."},
        {"text": "Ailovanta workers execute training jobs, submit artifacts, and earn trust through validation."},
        {"text": "Owned runtime means the route, artifact binding, worker result, and lineage are auditable."},
        {"text": "Distributed GPU workers should turn verified samples into candidate checkpoints."},
        {"text": "Ailovanta code intelligence focuses on instructions, syntax, tests, repair, and execution feedback."},
        {"text": "The training loop discovers sources, builds datasets, runs workers, validates outputs, and promotes artifacts."},
    ]
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed a real local training job for the Ailovanta worker")
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--dataset", default="runtime_data/local_training_seed.jsonl")
    parser.add_argument("--name", default="ailovanta-local-ngram")
    parser.add_argument("--base-model", default="ailovanta-bootstrap")
    parser.add_argument("--max-steps", type=int, default=8)
    args = parser.parse_args()

    dataset = write_seed_dataset((ROOT / args.dataset).resolve())
    result = post(
        args.server,
        "/training/jobs",
        {
            "kind": "lora_micro",
            "name": args.name,
            "dataset_uri": "file://" + str(dataset),
            "base_model": args.base_model,
            "max_steps": args.max_steps,
            "notes": "local real training smoke job; lightweight backend if transformers CUDA is unavailable",
        },
    )
    print(json.dumps({"ok": True, "dataset": str(dataset), "job": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
