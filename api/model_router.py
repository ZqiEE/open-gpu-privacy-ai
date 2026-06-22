from __future__ import annotations


class ModelRouter:
    def __init__(self, registry, inventory) -> None:
        self.registry = registry
        self.inventory = inventory

    def route(self, tag: str | None = None, min_score: float = 0.0, require_gpu: bool = False) -> dict:
        packages = self.registry.list_packages(min_score=min_score, tag=tag, limit=100)
        decisions = []
        for package in packages:
            nodes = self.inventory.nodes_for_package(package["package_hash"])
            if require_gpu:
                nodes = [node for node in nodes if node.get("has_gpu")]
            if not nodes:
                decisions.append({"package_hash": package["package_hash"], "name": package["name"], "version": package["version"], "routable": False, "reason": "no online node"})
                continue
            node = nodes[0]
            return {
                "routable": True,
                "package": package,
                "node": node,
                "reason": "best package with healthy node",
                "considered": decisions,
            }
        return {"routable": False, "package": None, "node": None, "reason": "no package matched", "considered": decisions}

    def route_by_hash(self, package_hash: str, require_gpu: bool = False) -> dict:
        package = self.registry.get_by_hash(package_hash)
        if not package:
            return {"routable": False, "reason": "package not found"}
        nodes = self.inventory.nodes_for_package(package_hash)
        if require_gpu:
            nodes = [node for node in nodes if node.get("has_gpu")]
        if not nodes:
            return {"routable": False, "package": package, "reason": "no online node"}
        return {"routable": True, "package": package, "node": nodes[0], "reason": "package found on node"}
