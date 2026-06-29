from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.code_task_builder import build_tasks_from_corpus


def main() -> int:
    parser = argparse.ArgumentParser(description="Build executable worker code tasks from instruction-first corpus")
    parser.add_argument("corpus")
    parser.add_argument("--output", default="runtime_data/code_instruction_tasks.json")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    result = build_tasks_from_corpus(args.corpus, args.output, limit=args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
