from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.code_failure_samples import export_failures_from_reports


def load_reports(path: str | Path) -> list[dict]:
    source = Path(path)
    if source.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    payload = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload.get("items"), list):
        return payload["items"]
    if isinstance(payload.get("reports"), list):
        return payload["reports"]
    return [payload]


def main() -> int:
    parser = argparse.ArgumentParser(description="Export failed code task runs as negative/repair training signals")
    parser.add_argument("reports")
    parser.add_argument("--output", default="runtime_data/failed_code_samples.json")
    args = parser.parse_args()
    result = export_failures_from_reports(load_reports(args.reports), args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
