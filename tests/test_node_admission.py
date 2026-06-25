from api.node_admission import admit_runtime_node, choose_allowed_pool, rules_summary


def test_rules_summary_contains_gpu_pools() -> None:
    rules = rules_summary()
    assert "small_gpu_pool" in rules
    assert "large_gpu_pool" in rules


def test_reject_small_gpu_without_memory() -> None:
    node = {"runtime_id": "rt1", "node_id": "n1", "pool": "small_gpu_pool", "status": "online", "gpu_memory_gb": 0, "available_gpu_memory_gb": 0, "trust_score": 0.9, "current_load": 0.1}
    result = admit_runtime_node(node)
    assert not result["ok"]
    assert "gpu_required" in result["blockers"]


def test_admit_large_gpu() -> None:
    node = {"runtime_id": "rt1", "node_id": "n1", "pool": "large_gpu_pool", "status": "online", "gpu_memory_gb": 48, "available_gpu_memory_gb": 40, "trust_score": 0.8, "current_load": 0.1}
    result = admit_runtime_node(node)
    assert result["ok"]
    assert result["decision"] == "admit"


def test_reject_validator_low_trust() -> None:
    node = {"runtime_id": "rt1", "node_id": "n1", "pool": "validator_pool", "status": "online", "gpu_memory_gb": 0, "available_gpu_memory_gb": 0, "trust_score": 0.2, "current_load": 0.1}
    result = admit_runtime_node(node)
    assert not result["ok"]
    assert "trust_score_too_low" in result["blockers"]


def test_choose_allowed_pool() -> None:
    assert choose_allowed_pool({"gpu_memory_gb": 0}, trust_score=0.5)["pool"] == "cpu_pool"
    assert choose_allowed_pool({"gpu_memory_gb": 8}, trust_score=0.4)["pool"] == "small_gpu_pool"
    assert choose_allowed_pool({"gpu_memory_gb": 32}, trust_score=0.6)["pool"] == "large_gpu_pool"
