from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any


SECRET_KEYS = {"api_key", "secret", "token", "password", "private_key"}


@dataclass(frozen=True)
class ProductionConfig:
    env: str
    public_base_url: str | None
    artifact_store: str
    artifact_store_uri: str | None
    chain_anchor: str
    chain_anchor_uri: str | None
    worker_mode: str
    model_backend: str
    node_trust_path: str
    runtime_path: str
    route_book_path: str
    require_node_proof: bool
    min_proof_coverage: float
    min_avg_trust_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def load_config() -> ProductionConfig:
    return ProductionConfig(
        env=os.getenv("AILOVANTA_ENV", "local"),
        public_base_url=os.getenv("AILOVANTA_PUBLIC_BASE_URL"),
        artifact_store=os.getenv("AILOVANTA_ARTIFACT_STORE", "local"),
        artifact_store_uri=os.getenv("AILOVANTA_ARTIFACT_STORE_URI"),
        chain_anchor=os.getenv("AILOVANTA_CHAIN_ANCHOR", "file"),
        chain_anchor_uri=os.getenv("AILOVANTA_CHAIN_ANCHOR_URI"),
        worker_mode=os.getenv("AILOVANTA_WORKER_MODE", "local"),
        model_backend=os.getenv("AILOVANTA_MODEL_BACKEND", "local"),
        node_trust_path=os.getenv("AILOVANTA_NODE_TRUST_PATH", "runtime_data/node_trust.sqlite3"),
        runtime_path=os.getenv("AILOVANTA_RUNTIME_PATH", "runtime_data/runtime.sqlite3"),
        route_book_path=os.getenv("AILOVANTA_ROUTE_BOOK_PATH", "runtime_data/route_book.sqlite3"),
        require_node_proof=bool_env("AILOVANTA_REQUIRE_NODE_PROOF", True),
        min_proof_coverage=float_env("AILOVANTA_MIN_PROOF_COVERAGE", 0.8),
        min_avg_trust_score=float_env("AILOVANTA_MIN_AVG_TRUST_SCORE", 0.75),
    )


def redacted_env() -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in sorted(os.environ.items()):
        if not key.startswith("AILOVANTA_"):
            continue
        lower = key.lower()
        if any(part in lower for part in SECRET_KEYS):
            out[key] = "***REDACTED***"
        else:
            out[key] = value
    return out
