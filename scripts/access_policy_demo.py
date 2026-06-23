from __future__ import annotations

import json

from api.execution_window import open_execution_window
from api.model_access_policy import ModelAccessPolicy
from api.model_package import build_model_package
from api.protected_model_package import build_protected_package
from api.quorum_policy import QuorumPolicy
from api.runtime_check import RuntimeCheckPolicy


def main() -> None:
    node = {"node_id": "node_policy_demo", "reputation": 0.9, "stake": 10, "attested": True}
    package = build_model_package("demo", "v1", "base", "a", "d", 0.9, "obj")
    guarded = build_protected_package(package, "confidential", {"required": 2, "total": 3}, "obj2")
    quorum = QuorumPolicy(2, 3).evaluate(["g1", "g2"])
    runtime_hash = "runtime_demo"
    runtime = RuntimeCheckPolicy({runtime_hash}).verify(node["node_id"], runtime_hash, "simulated-safe-box", {"node_id": node["node_id"]})
    window = open_execution_window(node["node_id"], guarded["package_hash"], "task_demo", runtime_hash, seconds=300)
    access = ModelAccessPolicy().decide(guarded["access_level"], node)
    print(json.dumps({"guarded": guarded, "quorum": quorum.__dict__, "runtime": runtime, "window": window, "access": access.__dict__}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
