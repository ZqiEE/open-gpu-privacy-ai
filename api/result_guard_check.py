from __future__ import annotations

from typing import Any

from api.node_proof import load_node_secrets
from api.wio import signed_result, verify_result


SAMPLE = {
    "task_id": "result_guard_check",
    "checkpoint_uri": "file:///tmp/ailovanta-result-guard.bin",
    "checkpoint_hash": "sha256:" + "0" * 64,
    "token_count": 0,
    "train_loss": 0.0,
    "eval_loss": 0.0,
}


def check_result_guard() -> dict[str, Any]:
    blockers: list[str] = []
    no_mark = verify_result({**SAMPLE, "node_id": "result-guard-node"})
    if no_mark.get("ok"):
        blockers.append("missing_node_mark_accepted")

    wrong = signed_result(SAMPLE, node_id="result-guard-node", secret="wrong-secret")
    wrong_checked = verify_result(wrong)
    if wrong_checked.get("ok"):
        blockers.append("wrong_node_mark_accepted")

    configured = load_node_secrets()
    good_checked = None
    if not configured:
        blockers.append("node_secret_map_missing")
    else:
        node_id, secret = next(iter(configured.items()))
        good = signed_result(SAMPLE, node_id=node_id, secret=secret)
        good_checked = verify_result(good)
        if not good_checked.get("ok"):
            reason = (good_checked.get("proof") or {}).get("reason") or good_checked.get("shape")
            blockers.append("configured_node_mark_rejected:" + str(reason))

    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "missing_check": no_mark,
        "wrong_check": wrong_checked,
        "configured_check": good_checked,
        "configured_secret_count": len(configured),
    }
