from __future__ import annotations

import argparse
import json

from api.model_warm import ModelWarm, WarmSpec
from api.owned_doctor import OwnedDoctor


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare model runtime when possible")
    parser.add_argument("--model-key", default="ailovanta-owned:candidate")
    parser.add_argument("--runtime-id", default="rt-owned-1")
    parser.add_argument("--node-id", default="node-owned-1")
    args = parser.parse_args()
    before = OwnedDoctor().check(args.model_key)
    action = ModelWarm().run(WarmSpec(model_key=args.model_key, runtime_id=args.runtime_id, node_id=args.node_id)) if not before.get("ok") else None
    after = OwnedDoctor().check(args.model_key)
    print(json.dumps({"ok": after.get("ok"), "before": before, "action": action, "after": after}, ensure_ascii=False, indent=2))
    return 0 if after.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
