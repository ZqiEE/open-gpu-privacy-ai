from __future__ import annotations


class ReputationService:
    def __init__(self, store) -> None:
        self.store = store

    def leaderboard(self, limit: int = 20) -> dict:
        nodes = self.store.list_nodes(limit=limit)
        ranked = [self._score_node(node) for node in nodes]
        ranked.sort(key=lambda item: item["reputation_score"], reverse=True)
        return {"nodes": ranked[:limit]}

    def summary(self) -> dict:
        nodes = self.leaderboard(limit=1000)["nodes"]
        if not nodes:
            return {"nodes": 0, "average_score": 0, "top_score": 0}
        total = sum(item["reputation_score"] for item in nodes)
        return {
            "nodes": len(nodes),
            "average_score": round(total / len(nodes), 2),
            "top_score": nodes[0]["reputation_score"],
        }

    @staticmethod
    def _score_node(node: dict) -> dict:
        base = int(node.get("trust", 30))
        compute = min(int(node.get("score", 0)) // 10, 25)
        gpu_bonus = 10 if node.get("has_gpu") else 0
        online_bonus = 5 if node.get("status") in {"online", "busy", "idle"} else 0
        reputation_score = max(0, min(100, base + compute + gpu_bonus + online_bonus))
        return {
            "node_id": node["node_id"],
            "device_name": node["device_name"],
            "status": node["status"],
            "trust": node["trust"],
            "compute_score": node["score"],
            "has_gpu": node["has_gpu"],
            "gpu_name": node.get("gpu_name"),
            "reputation_score": reputation_score,
            "last_seen": node.get("last_seen"),
        }
