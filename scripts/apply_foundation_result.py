from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.foundation_result_import import import_foundation_result_file
from api.model_warm import ModelWarm, WarmSpec
from api.owned_doctor import OwnedDoctor


def model_key_from_result(data: dict[str, Any]) -> str:
    model = data.get("runtime_model") or {}
    if model.get("model_key"):
        return str(model["model_key"])
    model_id = model.get("model_id") or "ailovanta-owned"
    version = model.get("version") or "candidate"
    return f"{model_id}:{version}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a foundation result to the owned runtime")
    parser.add_argument("result_path")
    parser.add_argument("--runtime-id", default="rt-owned-1")
    parser.add_argument("--node-id", default="node-owned-1")
    parser.add_argument("--gpu-memory-gb", type=float, default=24.0)
    parser.add_argument("--no-warm", action="store_true")
    args = parser.parse_args()

    applied = import_foundation_result_file(args.result_path)
    model_key = model_key_from_result(applied)
    warm = None
    if not args.no_warm:
        warm = ModelWarm().run(WarmSpec(model_key=model_key, runtime_id=args.runtime_id, node_id=args.node_id, gpu_memory_gb=args.gpu_memory_gb))
    doctor = OwnedDoctor().check(model_key)
    output = {"ok": bool(applied) and (args.no_warm or bool((warm or {}).get("ok"))), "model_key": model_key, "applied": applied, "warm": warm, "doctor": doctor}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
