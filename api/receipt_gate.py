from __future__ import annotations


def ready_for_catalog_publish(item: dict) -> dict:
    if not item.get("artifact_hash") and not item.get("digest"):
        return {"ok": False, "reason": "artifact hash required"}
    if not item.get("proof"):
        return {"ok": False, "reason": "worker receipt required"}
    if not item.get("anchor_receipt"):
        return {"ok": False, "reason": "anchor receipt required"}
    return {"ok": True}
