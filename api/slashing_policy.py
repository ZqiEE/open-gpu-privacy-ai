from __future__ import annotations


class SlashingPolicy:
    def evaluate(self, node: dict, incident: dict) -> dict:
        severity = incident.get("severity", "low")
        base = {"low": 0.1, "medium": 0.5, "high": 1.5, "critical": 5.0}.get(severity, 0.1)
        reputation = float(node.get("reputation", 0.0))
        stake = float(node.get("stake", 0.0))
        penalty = min(stake, base)
        new_reputation = max(0.0, round(reputation - base * 0.1, 3))
        return {
            "node_id": node.get("node_id", "unknown"),
            "incident_type": incident.get("type", "unknown"),
            "severity": severity,
            "penalty": round(penalty, 3),
            "new_reputation": new_reputation,
            "action": "ban" if severity == "critical" else "reduce_reputation",
        }
