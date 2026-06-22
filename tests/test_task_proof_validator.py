from __future__ import annotations

from api.network_validator import NetworkValidator
from api.task_proof import build_task_proof
from node_client.execution_report import build_execution_report
from node_client.job_runner import JobRunner


def test_task_proof_and_validator_score_ok_report() -> None:
    job = {"id": "job_eval", "type": "evaluation", "payload": {"samples": 1}}
    result = JobRunner().run(job)
    report = build_execution_report("node_validator", job, result)
    proof = build_task_proof(report)
    validation = NetworkValidator().score_proof(proof, report)
    assert proof["proof_id"].startswith("proof_")
    assert validation["node_id"] == "node_validator"
    assert validation["score"] > 0
    assert validation["credits"] > 0
