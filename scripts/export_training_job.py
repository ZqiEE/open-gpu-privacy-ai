from __future__ import annotations

import argparse
import json

from api.training_job_export import export_training_job


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a public training job for ailovanta-core")
    parser.add_argument("job_id")
    parser.add_argument("--output-dir", default="runtime_data/training_exports")
    args = parser.parse_args()

    result = export_training_job(args.job_id, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
