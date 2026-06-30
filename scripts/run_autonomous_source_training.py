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
    parser.add_argument("--frontier", default="runtime_data/github_source_frontier.json")
    parser.add_argument("--ledger", default="runtime_data/continuous_training_ledger.json")
    parser.add_argument("--work-root", default="runtime_data/autonomous_source_training")
    parser.add_argument("--no-discover", action="store_true")
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument("--max-sources", type=int, default=3)
    parser.add_argument("--max-discovery-queries", type=int, default=5)
    parser.add_argument("--max-records", type=int, default=512)
    parser.add_argument("--max-steps", type=int, default=16)
    parser.add_argument("--base-model", default="sshleifer/tiny-gpt2")
    parser.add_argument("--training-backend", choices=["lora", "qlora", "transformers"], default="lora")
    parser.add_argument("--allow-lightweight-fallback", action="store_true")
    parser.add_argument("--no-require-gpu", action="store_true")
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
            base_model=args.base_model,
            training_backend=args.training_backend,
            require_gpu=not args.no_require_gpu,
            allow_lightweight_fallback=args.allow_lightweight_fallback,
            frontier_path=args.frontier,
            max_discovery_queries=args.max_discovery_queries,
            ledger_path=args.ledger,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not args.loop:
            return 0 if result.get("ok") else 1
        time.sleep(max(60, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
