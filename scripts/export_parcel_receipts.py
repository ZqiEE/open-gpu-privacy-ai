from __future__ import annotations

import argparse
import json

from api.parcel_receipts import export_receipts


def main() -> int:
    parser = argparse.ArgumentParser(description="Export submitted parcels as checkpoint receipts")
    parser.add_argument("--output", default="runtime_data/parcels/checkpoint_receipts.json")
    args = parser.parse_args()
    result = export_receipts(output_path=args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
