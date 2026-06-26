from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.ckpt_manifest import make_manifest
from api.ckpt_run import newest_ref


def main() -> int:
    p = argparse.ArgumentParser(description="Create artifact manifest for checkpoint")
    p.add_argument("--ref")
    p.add_argument("--chunk-bytes", type=int, default=8 * 1024 * 1024)
    args = p.parse_args()
    ref = args.ref or newest_ref()
    if not ref:
        print(json.dumps({"ok": False, "error": "no checkpoint found"}, ensure_ascii=False, indent=2))
        return 1
    manifest = make_manifest(ref, chunk_bytes=args.chunk_bytes)
    print(json.dumps({"ok": True, "manifest": manifest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
