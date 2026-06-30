from __future__ import annotations

import argparse
import json

from api.foundation_pipeline import run_foundation_pipeline, write_pipeline_result
from api.verified_code_foundation import create_job_from_verified_code_export


def main() -> int:
    parser = argparse.ArgumentParser(description="Create and run a foundation job from verified code samples")
    parser.add_argument("verified_samples")
    parser.add_argument("--core-path", default=None)
    parser.add_argument("--work-dir", default="runtime_data/verified_code_foundation")
    parser.add_argument("--output", default="runtime_data/verified_code_foundation/pipeline_result.json")
    parser.add_argument("--model-id", default="ailovanta-code")
    parser.add_argument("--target-version", default="candidate")
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--simulate", action="store_true", help="plan only; do not execute local checkpoint training")
    parser.add_argument("--training-command", default=None)
    args = parser.parse_args()

    job = create_job_from_verified_code_export(
        args.verified_samples,
        model_id=args.model_id,
        target_version=args.target_version,
        max_steps=args.max_steps,
        execute_checkpoints=not args.simulate,
    )
    result = run_foundation_pipeline(
        job["job_id"],
        core_path=args.core_path,
        work_dir=args.work_dir,
        execute_checkpoints=not args.simulate,
        training_command=args.training_command,
    )
    result = {"ok": True, "foundation_job": job, "pipeline": result}
    write_pipeline_result(result, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
