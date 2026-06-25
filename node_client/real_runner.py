from __future__ import annotations

import time
from dataclasses import dataclass

from node_client.job_descriptor import JobDescriptorPolicy
from node_client.model_worker import run_model_shard, summary_json
from node_client.task_policy import TaskPolicy


@dataclass
class JobRunResult:
    job_id: str
    status: str
    output_summary: str
    runtime_seconds: float
    policy_reason: str = "accepted"
    descriptor_reason: str = "descriptor optional"


class JobRunner:
    def __init__(self, policy: TaskPolicy | None = None, descriptor_policy: JobDescriptorPolicy | None = None) -> None:
        self.policy = policy or TaskPolicy.default()
        self.descriptor_policy = descriptor_policy or JobDescriptorPolicy(required=False)

    def run(self, job: dict) -> JobRunResult:
        start = time.time()
        job_type = job.get("type", "unknown")
        descriptor_check = self.descriptor_policy.validate(job)
        if not descriptor_check.ok:
            return JobRunResult(job.get("id", "unknown"), "failed", f"descriptor: {descriptor_check.reason}", round(time.time() - start, 3), "descriptor", descriptor_check.reason)
        ok, reason = self.policy.validate(job)
        if not ok:
            return JobRunResult(job.get("id", "unknown"), "failed", reason, round(time.time() - start, 3), reason, descriptor_check.reason)
        if job_type == "model_shard":
            try:
                result = run_model_shard(job)
                return JobRunResult(job["id"], "ok", summary_json(result), round(time.time() - start, 3), reason, descriptor_check.reason)
            except Exception as exc:
                return JobRunResult(job.get("id", "unknown"), "failed", str(exc), round(time.time() - start, 3), "runtime_error", descriptor_check.reason)
        time.sleep(min(self._seconds(job_type), self.policy.max_runtime_seconds))
        return JobRunResult(job["id"], "ok", f"result for {job_type}", round(time.time() - start, 3), reason, descriptor_check.reason)

    @staticmethod
    def _seconds(job_type: str) -> float:
        return {"rag_index": 0.5, "rag_import": 0.6, "evaluation": 0.7, "evaluation_batch": 0.8, "verification": 0.4, "lora_micro": 1.0}.get(job_type, 0.6)
