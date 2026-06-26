from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.promote import gate


def main() -> int:
    p = argparse.ArgumentParser(description="Promote checkpoint if eval passes")
    p.add_argument("--manifest")
    p.add_argument("--eval-file", default="runtime_data/code_eval.json")
    p.add_argument("--min-score", type=float, default=1.0)
    args = p.parse_args()
    result = gate(args.manifest, args.eval_file, args.min_score)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
