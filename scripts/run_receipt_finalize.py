from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from api.parcel_receipts import export_receipts


def main() -> int:
    parser = argparse.ArgumentParser(description="Export submitted parcel receipts and aggregate them with ailovanta-core")
    parser.add_argument("--core-path", default="../ailovanta-core")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--receipts-output", default="runtime_data/parcels/checkpoint_receipts.json")
    parser.add_argument("--set-output", default="runtime_data/parcels/checkpoint_set.json")
    args = parser.parse_args()
    exported = export_receipts(output_path=args.receipts_output)
    if exported.get("count", 0) <= 0:
        print(json.dumps({"ok": False, "reason": "no receipts", "exported": exported}, ensure_ascii=False, indent=2))
        return 1
    core_root = Path(args.core_path).resolve()
    command = [sys.executable, str(core_root / "scripts" / "finalize_receipts.py"), str(Path(args.plan).resolve()), str(Path(args.receipts_output).resolve()), "--output", str(Path(args.set_output).resolve())]
    proc = subprocess.run(command, cwd=core_root, check=True, text=True, capture_output=True)
    core_result = json.loads(proc.stdout)
    print(json.dumps({"ok": True, "exported": exported, "core": core_result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
