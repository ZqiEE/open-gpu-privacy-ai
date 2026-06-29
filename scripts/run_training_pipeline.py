from __future__ import annotations

import argparse
import json

from api.training_pipeline import run_training_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a public training job through ailovanta-core")
    parser.add_argument("job_id")
    parser.add_argument("--core-path", default=None)
    parser.add_argument("--work-dir", default="runtime_data/training_pipeline")
    args = parser.parse_args()

    result = run_training_pipeline(args.job_id, core_path=args.core_path, work_dir=args.work_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
