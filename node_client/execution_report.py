from __future__ import annotations

from dataclasses import asdict, dataclass
from time import time

from node_client.job_descriptor import JobDescriptorPolicy


@dataclass
class ExecutionReport:
    report_id: str
    node_id: str
    job_id: str
    job_type: str
    status: str
    runtime_seconds: float
    policy_reason: str
    descriptor_ok: bool
    descriptor_reason: str
    created_at: float


def build_execution_report(node_id: str, job: dict, result) -> dict:
    descriptor_check = JobDescriptorPolicy(required=False).validate(job)
    report = ExecutionReport(
        report_id=f"report_{node_id}_{job.get('id', 'unknown')}",
        node_id=node_id,
        job_id=job.get("id", "unknown"),
        job_type=job.get("type", "unknown"),
        status=result.status,
        runtime_seconds=result.runtime_seconds,
        policy_reason=getattr(result, "policy_reason", "unknown"),
        descriptor_ok=descriptor_check.ok,
        descriptor_reason=descriptor_check.reason,
        created_at=round(time(), 3),
    )
    return asdict(report)
