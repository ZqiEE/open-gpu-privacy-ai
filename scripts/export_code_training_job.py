from __future__ import annotations

import argparse
import json
from pathlib import Path

from api.code_training_jobs import CodeTrainingJobStore
from api.rights_proof_registry import RightsProofRegistry


def main() -> int:
    parser = argparse.ArgumentParser(description="Export an Ailovanta-Code distributed training job")
    parser.add_argument("--rights-id", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--kind", default="code_lora")
    parser.add_argument("--base-model", default="ailovanta-code-bootstrap")
    parser.add_argument("--target-model", default="ailovanta-code")
    parser.add_argument("--rights-path", default="runtime_data/rights_proofs.json")
    parser.add_argument("--jobs-path", default="runtime_data/code_training_jobs.json")
    parser.add_argument("--output", default="runtime_data/code_training_job.json")
    args = parser.parse_args()

    registry = RightsProofRegistry(args.rights_path)
    store = CodeTrainingJobStore(args.jobs_path, rights_registry=registry)
    job = store.create_job(
        rights_id=args.rights_id,
        dataset_id=args.dataset_id,
        kind=args.kind,
        base_model=args.base_model,
        target_model=args.target_model,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "job_id": job["job_id"], "distributed_required": job["distributed_required"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
