from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChainReceipt:
    ok: bool
    adapter: str
    action: str
    reference: str
    payload_hash: str
    message: str


class ChainAdapter(ABC):
    name: str

    @abstractmethod
    def submit_event(self, event: dict[str, Any]) -> ChainReceipt:
        raise NotImplementedError

    @abstractmethod
    def submit_model_commit(self, commit: dict[str, Any]) -> ChainReceipt:
        raise NotImplementedError

    @abstractmethod
    def status(self) -> dict[str, Any]:
        raise NotImplementedError
