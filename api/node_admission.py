from __future__ import annotations

from dataclasses import asdict, dataclass
from time import time
from typing import Any


GPU_POOLS = {"small_gpu_pool", "large_gpu_pool", "trusted_runtime_pool", "enterprise_pool"}
PUBLIC_POOLS = {"cpu_pool", "small_gpu_pool", "large_gpu_pool", "storage_pool", "validator_pool"}


@dataclass(frozen=True)
class AdmissionRule:
    pool: str
    min_gpu_memory_gb: float = 0.0
    min_trust_score: float = 0.0
    max_current_load: float = 0.95
    heartbeat_ttl_seconds: float = 180.0
    requires_gpu: bool = False
    public_allowed: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEFAULT_RULES: dict[str, AdmissionRule] = {
    "cpu_pool": AdmissionRule("cpu_pool", min_trust_score=0.1, requires_gpu=False),
    "small_gpu_pool": AdmissionRule("small_gpu_pool", min_gpu_memory_gb=4.0, min_trust_score=0.25, requires_gpu=True),
    "large_gpu_pool": AdmissionRule("large_gpu_pool", min_gpu_memory_gb=24.0, min_trust_score=0.45, requires_gpu=True),
    "storage_pool": AdmissionRule("storage_pool", min_trust_score=0.2, requires_gpu=False),
    "validator_pool": AdmissionRule("validator_pool", min_trust_score=0.55, max_current_load=0.8, requires_gpu=False),
    "trusted_runtime_pool": AdmissionRule("trusted_runtime_pool", min_gpu_memory_gb=16.0, min_trust_score=0.8, max_current_load=0.75, requires_gpu=True, public_allowed=False),
    "enterprise_pool": AdmissionRule("enterprise_pool", min_gpu_memory_gb=16.0, min_trust_score=0.9, max_current_load=0.75, requires_gpu=True, public_allowed=False),
}


def admit_runtime_node(node: dict[str, Any], now: float | None = None, rules: dict[str, AdmissionRule] | None = None) -> dict[str, Any]:
    rules = rules or DEFAULT_RULES
    now = now or time()
    pool = str(node.get("pool") or "")
    rule = rules.get(pool)
    blockers: list[str] = []
    warnings: list[str] = []

    if rule is None:
        blockers.append("unknown_pool")
        return {"ok": False, "pool": pool, "decision": "reject", "blockers": blockers, "warnings": warnings, "rule": None}

    status = str(node.get("status") or "offline")
    gpu_memory = float(node.get("gpu_memory_gb") or 0.0)
    available_gpu_memory = float(node.get("available_gpu_memory_gb") or 0.0)
    trust = float(node.get("trust_score") or 0.0)
    load = float(node.get("current_load") or 0.0)
    last_heartbeat = float(node.get("last_heartbeat") or 0.0)

    if status not in {"online", "idle"}:
        blockers.append("node_not_online")
    if rule.requires_gpu and gpu_memory <= 0:
        blockers.append("gpu_required")
    if gpu_memory < rule.min_gpu_memory_gb:
        blockers.append("insufficient_gpu_memory")
    if available_gpu_memory < min(rule.min_gpu_memory_gb, gpu_memory):
        warnings.append("low_available_gpu_memory")
    if trust < rule.min_trust_score:
        blockers.append("trust_score_too_low")
    if load > rule.max_current_load:
        blockers.append("node_overloaded")
    if last_heartbeat and now - last_heartbeat > rule.heartbeat_ttl_seconds:
        blockers.append("heartbeat_stale")
    if pool in {"trusted_runtime_pool", "enterprise_pool"} and rule.public_allowed:
        blockers.append("trusted_pool_misconfigured")

    decision = "admit" if not blockers else "reject"
    return {"ok": not blockers, "decision": decision, "pool": pool, "blockers": blockers, "warnings": warnings, "rule": rule.to_dict(), "node_id": node.get("node_id"), "runtime_id": node.get("runtime_id")}


def choose_allowed_pool(node: dict[str, Any], trust_score: float | None = None) -> dict[str, Any]:
    trust = float(trust_score if trust_score is not None else node.get("trust_score") or 0.5)
    gpu_memory = float(node.get("gpu_memory_gb") or node.get("memory_total_gb") or 0.0)
    has_gpu = gpu_memory > 0
    if not has_gpu:
        pool = "cpu_pool" if trust >= DEFAULT_RULES["cpu_pool"].min_trust_score else "pending"
    elif gpu_memory >= DEFAULT_RULES["large_gpu_pool"].min_gpu_memory_gb and trust >= DEFAULT_RULES["large_gpu_pool"].min_trust_score:
        pool = "large_gpu_pool"
    elif gpu_memory >= DEFAULT_RULES["small_gpu_pool"].min_gpu_memory_gb and trust >= DEFAULT_RULES["small_gpu_pool"].min_trust_score:
        pool = "small_gpu_pool"
    else:
        pool = "pending"
    return {"pool": pool, "trust_score": trust, "gpu_memory_gb": gpu_memory, "has_gpu": has_gpu}


def rules_summary() -> dict[str, Any]:
    return {name: rule.to_dict() for name, rule in DEFAULT_RULES.items()}
