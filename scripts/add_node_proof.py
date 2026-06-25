from __future__ import annotations

import argparse
import json
from pathlib import Path

from api.node_proof import attach_proof, verify_proof


def main() -> int:
    parser = argparse.ArgumentParser(description="Attach or verify a node proof for a submitted payload")
    parser.add_argument("input")
    parser.add_argument("--output", default=None)
    parser.add_argument("--node-id", required=True)
    parser.add_argument("--secret", required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if args.verify:
        result = verify_proof(data, {args.node_id: args.secret})
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1
    signed = attach_proof(data, args.node_id, args.secret)
    output = Path(args.output or args.input)
    output.write_text(json.dumps(signed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "proof": signed.get("node_proof")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
