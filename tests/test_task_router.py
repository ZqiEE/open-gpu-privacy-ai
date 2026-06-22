from __future__ import annotations

from api.task_router import TaskRouter


def test_gpu_job_requires_gpu_node() -> None:
    router = TaskRouter()
    cpu_node = {"node_id": "cpu", "has_gpu": False, "memory_gb": 16, "cpu_threads": 8}
    gpu_job = {"job_id": "job1", "job_type": "lora_micro", "payload_json": '{"requires_gpu": true}'}
    ok, reason = router.can_assign(cpu_node, gpu_job)
    assert ok is False
    assert reason == "requires gpu"


def test_cpu_job_matches_cpu_node() -> None:
    router = TaskRouter()
    cpu_node = {"node_id": "cpu", "has_gpu": False, "memory_gb": 16, "cpu_threads": 8}
    job = {"job_id": "job2", "job_type": "rag_index", "payload_json": '{"min_memory_gb": 4}'}
    ok, reason = router.can_assign(cpu_node, job)
    assert ok is True
    assert reason == "matched"


def test_priority_uses_payload_override() -> None:
    router = TaskRouter()
    job = {"job_id": "job3", "job_type": "evaluation", "payload_json": '{"priority": 99}'}
    assert router.job_priority(job) == 99
