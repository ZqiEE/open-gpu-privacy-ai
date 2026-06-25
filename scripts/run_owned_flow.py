from __future__ import annotations

import argparse
import json

import httpx

from api.model_warm import ModelWarm, WarmSpec
from api.route_gate import apply_gate


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare model runtime and call owned chat checked endpoint")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--model-key", default="ailovanta-owned:candidate")
    parser.add_argument("--prompt", default="hello")
    parser.add_argument("--runtime-id", default="rt-owned-1")
    parser.add_argument("--node-id", default="node-owned-1")
    args = parser.parse_args()
    model_id, version = args.model_key.split(":", 1)
    gate = apply_gate(model_id, version, "owned-flow")
    if gate is not None:
        print(json.dumps({"ok": False, "stage": "ref", "gate": gate}, ensure_ascii=False, indent=2))
        return 1
    online = ModelWarm().run(WarmSpec(model_key=args.model_key, runtime_id=args.runtime_id, node_id=args.node_id))
    if not online.get("ok"):
        print(json.dumps({"ok": False, "stage": "online", "online": online}, ensure_ascii=False, indent=2))
        return 1
    with httpx.Client(timeout=120) as client:
        response = client.post(args.api_url.rstrip("/") + "/ailovanta/v1/owned-chat-checked", json={"prompt": args.prompt, "model_id": model_id, "version": version})
        response.raise_for_status()
        chat = response.json()
    print(json.dumps({"ok": bool(chat.get("ok")), "online": online, "chat": chat}, ensure_ascii=False, indent=2))
    return 0 if chat.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
