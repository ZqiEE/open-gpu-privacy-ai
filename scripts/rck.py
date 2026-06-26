from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.ckpt_run import newest_ref, run_ckpt


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--text", required=True)
    p.add_argument("--ref")
    p.add_argument("--max-new", type=int, default=80)
    args = p.parse_args()
    ref = args.ref or newest_ref()
    if not ref:
        print(json.dumps({"ok": False, "error": "no checkpoint found"}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"ok": True, **run_ckpt(args.text, ref, args.max_new)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
