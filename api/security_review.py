from __future__ import annotations

import os
from typing import Any

from api.prod_config import load_config, redacted_env


DANGEROUS_PUBLIC_LOCAL_VALUES = {"local", "file"}
REQUIRED_SECRET_NAMES = ("AILOVANTA_ADMIN_TOKEN",)


def bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def secret_present(name: str) -> bool:
    value = os.getenv(name, "")
    return bool(value and value.strip() and value != "replace-me")


def public_url_ok(value: str | None) -> bool:
    return bool(value and value.startswith("https://"))


def check_secret_redaction() -> dict[str, Any]:
    env = redacted_env()
    leaked: list[str] = []
    for key, value in env.items():
        lower = key.lower()
        if any(part in lower for part in ("secret", "token", "password", "private_key")) and value != "***REDACTED***":
            leaked.append(key)
    return {"ok": not leaked, "leaked_keys": leaked}


def run_security_review() -> dict[str, Any]:
    cfg = load_config()
    blockers: list[str] = []
    warnings: list[str] = []

    if cfg.env == "production" and not public_url_ok(cfg.public_base_url):
        blockers.append("public_base_url_must_be_https")
    if cfg.env == "production" and cfg.artifact_store in DANGEROUS_PUBLIC_LOCAL_VALUES:
        blockers.append("production_artifact_store_is_local")
    if cfg.env == "production" and cfg.chain_anchor in DANGEROUS_PUBLIC_LOCAL_VALUES:
        blockers.append("production_anchor_is_local")
    if cfg.env == "production" and cfg.worker_mode == "local":
        blockers.append("production_worker_mode_is_local")
    if cfg.env == "production" and cfg.model_backend == "local":
        blockers.append("production_model_backend_is_local")
    if cfg.env == "production" and not cfg.require_node_proof:
        blockers.append("node_proof_required_in_production")
    if cfg.min_avg_trust_score < 0.75:
        warnings.append("min_trust_score_below_recommended")
    if not bool_env("AILOVANTA_RATE_LIMIT_ENABLED", False):
        blockers.append("rate_limit_disabled")
    for name in REQUIRED_SECRET_NAMES:
        if not secret_present(name):
            blockers.append("missing_secret:" + name)
    redaction = check_secret_redaction()
    if not redaction.get("ok"):
        blockers.append("secret_redaction_failed")
    if not cfg.use_postgres and cfg.env == "production":
        warnings.append("production_database_not_postgres")
    if not cfg.use_redis and cfg.env == "production":
        warnings.append("production_redis_not_enabled")

    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "config": cfg.to_dict(),
        "redaction": redaction,
        "checks": {
            "https_public_url": public_url_ok(cfg.public_base_url),
            "rate_limit_enabled": bool_env("AILOVANTA_RATE_LIMIT_ENABLED", False),
            "admin_token_present": secret_present("AILOVANTA_ADMIN_TOKEN"),
            "node_proof_required": cfg.require_node_proof,
        },
    }
