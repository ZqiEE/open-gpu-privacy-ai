from __future__ import annotations

import json


GPU_JOB_TYPES = {"lora_micro", "image_generation", "gpu_inference"}
HEAVY_JOB_TYPES = {"lora_micro", "rag_import", "evaluation_batch"}


class TaskRouter:
    def job_priority(self, job: dict) -> int:
        payload = self.payload(job)
        if "priority" in payload:
            return int(payload["priority"])
        job_type = job.get("job_type") or job.get("type")
        if job_type in GPU_JOB_TYPES:
            return 80
        if job_type in HEAVY_JOB_TYPES:
            return 60
        return 40

    def can_assign(self, node: dict, job: dict) -> tuple[bool, str]:
        payload = self.payload(job)
        job_type = job.get("job_type") or job.get("type")
        requires_gpu = bool(payload.get("requires_gpu")) or job_type in GPU_JOB_TYPES
        min_memory_gb = float(payload.get("min_memory_gb", 0) or 0)
        min_cpu_threads = int(payload.get("min_cpu_threads", 0) or 0)

        if requires_gpu and not node.get("has_gpu"):
            return False, "requires gpu"
        if min_memory_gb and float(node.get("memory_gb", 0)) < min_memory_gb:
            return False, "not enough memory"
        if min_cpu_threads and int(node.get("cpu_threads", 0)) < min_cpu_threads:
            return False, "not enough cpu"
        return True, "matched"

    def explain(self, node: dict, job: dict) -> dict:
        ok, reason = self.can_assign(node, job)
        return {
            "matched": ok,
            "reason": reason,
            "priority": self.job_priority(job),
            "node_id": node.get("node_id"),
            "job_id": job.get("job_id") or job.get("id"),
            "job_type": job.get("job_type") or job.get("type"),
            "node_has_gpu": bool(node.get("has_gpu")),
            "node_memory_gb": node.get("memory_gb"),
            "node_cpu_threads": node.get("cpu_threads"),
        }

    @staticmethod
    def payload(job: dict) -> dict:
        value = job.get("payload")
        if isinstance(value, dict):
            return value
        raw = job.get("payload_json")
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
