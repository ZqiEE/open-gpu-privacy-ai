from __future__ import annotations

import time
from dataclasses import dataclass

from node_client.code_task_runner import run_code_instruction_task
from node_client.job_descriptor import JobDescriptorPolicy
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
    """Safe simulated runner for local MVP nodes.

    It does not execute arbitrary code. It validates task type, payload size,
    and optional job descriptor before returning a structured result.
    """

    def __init__(self, policy: TaskPolicy | None = None, descriptor_policy: JobDescriptorPolicy | None = None) -> None:
        self.policy = policy or TaskPolicy.default()
        self.descriptor_policy = descriptor_policy or JobDescriptorPolicy(required=False)

    def run(self, job: dict) -> JobRunResult:
        start = time.time()
        job_type = job.get("type", "unknown")
        descriptor_check = self.descriptor_policy.validate(job)
        if not descriptor_check.ok:
            return JobRunResult(
                job_id=job.get("id", "unknown"),
                status="failed",
                output_summary=f"rejected by descriptor policy: {descriptor_check.reason}",
                runtime_seconds=round(time.time() - start, 3),
                policy_reason="descriptor rejected",
                descriptor_reason=descriptor_check.reason,
            )
        ok, reason = self.policy.validate(job)
        if not ok:
            return JobRunResult(
                job_id=job.get("id", "unknown"),
                status="failed",
                output_summary=f"rejected by worker policy: {reason}",
                runtime_seconds=round(time.time() - start, 3),
                policy_reason=reason,
                descriptor_reason=descriptor_check.reason,
            )

        simulated_seconds = min(self._simulated_seconds(job_type), self.policy.max_runtime_seconds)
        time.sleep(simulated_seconds)
        runtime = round(time.time() - start, 3)
        if runtime > self.policy.max_runtime_seconds:
            return JobRunResult(
                job_id=job["id"],
                status="failed",
                output_summary="worker timeout",
                runtime_seconds=runtime,
                policy_reason="timeout",
                descriptor_reason=descriptor_check.reason,
            )
        if job_type == "code_instruction_eval":
            run = run_code_instruction_task(job)
            return JobRunResult(
                job_id=job["id"],
                status="ok" if run.passed else "failed",
                output_summary=json_summary(run.report),
                runtime_seconds=run.report["runtime_seconds"],
                policy_reason=reason,
                descriptor_reason=descriptor_check.reason,
            )
        return JobRunResult(
            job_id=job["id"],
            status="ok",
            output_summary=f"simulated safe result for {job_type}",
            runtime_seconds=runtime,
            policy_reason=reason,
            descriptor_reason=descriptor_check.reason,
        )

    @staticmethod
    def _simulated_seconds(job_type: str) -> float:
        return {
            "rag_index": 0.5,
            "rag_import": 0.6,
            "evaluation": 0.7,
            "evaluation_batch": 0.8,
            "verification": 0.4,
            "lora_micro": 1.0,
            "model_shard": 1.0,
        }.get(job_type, 0.6)


def json_summary(report: dict) -> str:
    import json

    return json.dumps(report, ensure_ascii=False, sort_keys=True)
