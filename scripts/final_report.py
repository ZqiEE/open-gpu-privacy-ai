from __future__ import annotations

import argparse
import json

from api.final_report import report


def main() -> int:
    p = argparse.ArgumentParser(description="Show final runtime report")
    p.add_argument("result")
    p.add_argument("--model-key", default="ailovanta-owned:candidate")
    a = p.parse_args()
    data = report(a.result, model_key=a.model_key)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0 if data.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
