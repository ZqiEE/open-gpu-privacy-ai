from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.autonomous_source_training import run_autonomous_source_training_cycle


def main() -> int:
    parser = argparse.ArgumentParser(description="Automatically discover sources, ingest code, and queue training jobs")
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--sources", default="runtime_data/github_code_sources.json")
    parser.add_argument("--work-root", default="runtime_data/autonomous_source_training")
    parser.add_argument("--no-discover", action="store_true")
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument("--max-sources", type=int, default=3)
    parser.add_argument("--max-records", type=int, default=512)
    parser.add_argument("--max-steps", type=int, default=16)
    parser.add_argument("--corpus-mode", choices=["instructions", "code", "mixed"], default="mixed")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval", type=int, default=1800)
    args = parser.parse_args()

    while True:
        result = run_autonomous_source_training_cycle(
            server=args.server,
            sources_path=args.sources,
            work_root=args.work_root,
            discover=not args.no_discover,
            fetch=not args.no_fetch,
            max_sources=args.max_sources,
            max_records=args.max_records,
            corpus_mode=args.corpus_mode,
            max_steps=args.max_steps,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not args.loop:
            return 0 if result.get("ok") else 1
        time.sleep(max(60, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
