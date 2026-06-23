from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class QuorumDecision:
    passed: bool
    required: int
    provided: int
    reason: str


class QuorumPolicy:
    def __init__(self, required: int, total: int) -> None:
        if required <= 0 or total <= 0 or required > total:
            raise ValueError("invalid quorum policy")
        self.required = required
        self.total = total

    def evaluate(self, approvals: list[str]) -> QuorumDecision:
        unique = sorted(set(approvals))
        provided = len(unique)
        if provided >= self.required:
            return QuorumDecision(True, self.required, provided, "quorum accepted")
        return QuorumDecision(False, self.required, provided, "not enough approvals")

    def to_dict(self) -> dict:
        return {"required": self.required, "total": self.total}

    @staticmethod
    def from_dict(value: dict) -> "QuorumPolicy":
        return QuorumPolicy(required=int(value["required"]), total=int(value["total"]))


def quorum_result_dict(policy: QuorumPolicy, approvals: list[str]) -> dict:
    return asdict(policy.evaluate(approvals))
