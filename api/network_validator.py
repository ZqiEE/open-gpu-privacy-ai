from __future__ import annotations


class NetworkValidator:
    def score_proof(self, proof: dict, report: dict) -> dict:
        score = 0.0
        reasons: list[str] = []

        if proof.get("result_status") == "ok" and report.get("status") == "ok":
            score += 1.0
            reasons.append("status ok")
        else:
            score -= 0.5
            reasons.append("status not ok")

        if report.get("descriptor_ok") is True:
            score += 0.25
            reasons.append("descriptor ok")
        else:
            score += 0.05
            reasons.append("descriptor optional or missing")

        runtime = float(report.get("runtime_seconds", 0) or 0)
        if runtime <= 2.0:
            score += 0.25
            reasons.append("runtime healthy")
        elif runtime <= 10.0:
            score += 0.1
            reasons.append("runtime acceptable")
        else:
            score -= 0.25
            reasons.append("runtime slow")

        score = max(0.0, round(score, 3))
        credits = round(score * 10, 3)
        return {
            "proof_id": proof["proof_id"],
            "node_id": proof["node_id"],
            "score": score,
            "credits": credits,
            "passed": score >= 0.8,
            "reasons": reasons,
        }
