from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.code_repair_loop import repair_failures_from_reports
from scripts.export_failed_code_samples import load_reports


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate and verify repair candidates from failed code task reports")
    parser.add_argument("reports")
    parser.add_argument("--output", default="runtime_data/code_repair_results.json")
    parser.add_argument("--max-candidates-per-failure", type=int, default=16)
    parser.add_argument("--candidate-command", default=None)
    parser.add_argument("--backend-ref", default=None)
    args = parser.parse_args()
    result = repair_failures_from_reports(
        load_reports(args.reports),
        args.output,
        max_candidates_per_failure=args.max_candidates_per_failure,
        candidate_command=args.candidate_command,
        backend_ref=args.backend_ref,
    )
    print(json.dumps({key: value for key, value in result.items() if key != "verified_report_items"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
