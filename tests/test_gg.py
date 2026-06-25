from api.g2 import eval_payload


def test_gg_payload_has_guard_metrics() -> None:
    result = {"artifact": {"model_id": "m", "version": "v", "artifact_hash": "sha256:a", "metrics": {"proof_coverage": 0.9, "avg_trust_score": 0.8, "avg_eval_loss": 0.2, "accepted_checkpoints": 1}}}
    payload = eval_payload(result)
    names = [item["name"] for item in payload["metrics"]]
    assert "proof_coverage" in names
    assert "avg_trust_score" in names
    assert payload["guardrails"]["proof_coverage"] == 0.9
