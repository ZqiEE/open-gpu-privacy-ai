from __future__ import annotations

import argparse
import json

from api.foundation_pipeline import run_foundation_pipeline, write_pipeline_result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run public -> core -> public foundation pipeline")
    parser.add_argument("job_id")
    parser.add_argument("--core-path", default=None)
    parser.add_argument("--work-dir", default="runtime_data/foundation_pipeline")
    parser.add_argument("--output", default="runtime_data/foundation_pipeline/pipeline_result.json")
    args = parser.parse_args()

    result = run_foundation_pipeline(args.job_id, core_path=args.core_path, work_dir=args.work_dir)
    write_pipeline_result(result, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
