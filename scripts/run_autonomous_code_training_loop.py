from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.autonomous_code_training_loop import AutonomousCodeTrainingLoop


def main() -> int:
    parser = argparse.ArgumentParser(description="Run autonomous Ailovanta-Code discovery, verification, and training loop")
    parser.add_argument("--sources", default="runtime_data/github_code_sources.json")
    parser.add_argument("--core-path", default="../ailovanta-core")
    parser.add_argument("--root", default="runtime_data/autonomous_code_loop")
    parser.add_argument("--discover", action="store_true")
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument("--corpus-mode", choices=["instructions", "mixed"], default="instructions")
    parser.add_argument("--max-sources", type=int, default=None)
    parser.add_argument("--max-tasks", type=int, default=50)
    parser.add_argument("--skip-foundation", action="store_true")
    parser.add_argument("--simulate-foundation", action="store_true")
    parser.add_argument("--model-id", default="ailovanta-code")
    parser.add_argument("--target-version", default="candidate")
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--training-command", default=None)
    parser.add_argument("--no-repair", action="store_true")
    parser.add_argument("--max-repair-candidates", type=int, default=16)
    parser.add_argument("--repair-candidate-command", default=None)
    parser.add_argument("--repair-backend-ref", default=None)
    args = parser.parse_args()

    result = AutonomousCodeTrainingLoop(core_path=args.core_path, root=args.root).run_once(
        sources_path=args.sources,
        discover=args.discover,
        fetch=not args.no_fetch,
        corpus_mode=args.corpus_mode,
        max_sources=args.max_sources,
        max_tasks=args.max_tasks,
        run_foundation=not args.skip_foundation,
        execute_checkpoints=not args.simulate_foundation,
        model_id=args.model_id,
        target_version=args.target_version,
        max_steps=args.max_steps,
        training_command=args.training_command,
        repair_failures=not args.no_repair,
        max_repair_candidates=args.max_repair_candidates,
        repair_candidate_command=args.repair_candidate_command,
        repair_backend_ref=args.repair_backend_ref,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
