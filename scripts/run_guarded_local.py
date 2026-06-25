from __future__ import annotations

import argparse
import json

from api.learning_gate import run_guarded_learning_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Run guarded learning pipeline locally")
    parser.add_argument("--core-path", default="../ailovanta-core")
    parser.add_argument("--work-dir", default="runtime_data/guarded_learning_pipeline")
    parser.add_argument("--baseline-score", type=float, default=0.45)
    parser.add_argument("--allow-shadow-import", action="store_true")
    parser.add_argument("--execute-checkpoints", action="store_true")
    parser.add_argument("--model-backend", default=None)
    parser.add_argument("--base-model", default=None)
    parser.add_argument("--backend-device", default=None)
    parser.add_argument("--backend-max-steps", type=int, default=None)
    parser.add_argument("--no-prepare-runtime", action="store_true")
    args = parser.parse_args()
    result = run_guarded_learning_pipeline(
        core_path=args.core_path,
        work_dir=args.work_dir,
        baseline_score=args.baseline_score,
        allow_shadow_import=args.allow_shadow_import,
        execute_checkpoints=args.execute_checkpoints,
        model_backend=args.model_backend,
        base_model=args.base_model,
        backend_device=args.backend_device,
        backend_max_steps=args.backend_max_steps,
        prepare_runtime=not args.no_prepare_runtime,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
