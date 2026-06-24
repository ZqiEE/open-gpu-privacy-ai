from __future__ import annotations

import argparse
import json

from api.foundation_job_export import export_foundation_job


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a public foundation job for ailovanta-core")
    parser.add_argument("job_id")
    parser.add_argument("--output-dir", default="runtime_data/foundation_exports")
    args = parser.parse_args()
    result = export_foundation_job(args.job_id, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
