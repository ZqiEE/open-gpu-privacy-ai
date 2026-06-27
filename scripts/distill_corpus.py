from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.distill_data import build_distill_records, write_distill_jsonl


def main() -> int:
    p = argparse.ArgumentParser(description="Build distillation corpus from teacher JSONL")
    p.add_argument("--input", required=True)
    p.add_argument("--output", default="runtime_data/distill_corpus.jsonl")
    p.add_argument("--min-score", type=float, default=0.0)
    args = p.parse_args()
    records = build_distill_records(args.input, args.min_score)
    result = write_distill_jsonl(records, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if records else 1


if __name__ == "__main__":
    raise SystemExit(main())
