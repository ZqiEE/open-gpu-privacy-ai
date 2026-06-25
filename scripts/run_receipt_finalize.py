from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from api.parcel_receipts import export_receipts


def run_json(command: list[str], cwd: Path) -> dict:
    proc = subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True)
    return json.loads(proc.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export submitted parcel receipts and build distributed artifact")
    parser.add_argument("--core-path", default="../ailovanta-core")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--receipts-output", default="runtime_data/parcels/checkpoint_receipts.json")
    parser.add_argument("--set-output", default="runtime_data/parcels/checkpoint_set.json")
    parser.add_argument("--artifact-output", default="runtime_data/parcels/foundation_result.json")
    args = parser.parse_args()
    exported = export_receipts(output_path=args.receipts_output)
    if exported.get("count", 0) <= 0:
        print(json.dumps({"ok": False, "reason": "no receipts", "exported": exported}, ensure_ascii=False, indent=2))
        return 1
    core_root = Path(args.core_path).resolve()
    plan_path = Path(args.plan).resolve()
    receipts_path = Path(args.receipts_output).resolve()
    set_path = Path(args.set_output).resolve()
    artifact_path = Path(args.artifact_output).resolve()
    set_result = run_json([sys.executable, str(core_root / "scripts" / "finalize_receipts.py"), str(plan_path), str(receipts_path), "--output", str(set_path)], cwd=core_root)
    artifact_result = run_json([sys.executable, str(core_root / "scripts" / "make_artifact.py"), str(plan_path), str(set_path), "--output", str(artifact_path)], cwd=core_root)
    print(json.dumps({"ok": True, "exported": exported, "checkpoint_set": set_result, "artifact": artifact_result, "artifact_output": str(artifact_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
