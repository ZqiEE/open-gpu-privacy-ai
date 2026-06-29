from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from api.code_data import build_records, last_stats
from api.code_instruction_data import build_instruction_records
from api.code_instruction_data import last_stats as instruction_last_stats
from api.code_training_jobs import CodeTrainingJobStore
from api.rights_proof_registry import RightsProofRegistry

AUTHORIZED_POLICIES = {
    "owner_controlled",
    "explicit_permission",
    "internal",
    "shareholder_authorized",
    "private_owner_unrestricted",
    "authorized_unrestricted",
    "user_authorized",
}
PERMISSIVE_HINTS = {"mit", "apache", "apache-2.0", "bsd", "bsd-2-clause", "bsd-3-clause", "isc", "mpl", "mpl-2.0", "unlicense", "cc0"}
BLOCKED_HINTS = {"gpl", "lgpl", "agpl", "sspl", "unknown"}
DEFAULT_TRAINING_TYPES = ["code_lora", "code_qlora", "code_distill", "code_eval"]


def stable_id(prefix: str, value: str) -> str:
    return prefix + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def safe_name(value: str) -> str:
    parsed = urlparse(value)
    raw = Path(parsed.path).name or value
    raw = raw.removesuffix(".git")
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in raw)
    return cleaned[:80] or "source"


def load_sources(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [dict(item) for item in payload.get("sources", []) if item.get("enabled", True)]


def source_allowed(source: dict[str, Any]) -> tuple[bool, str]:
    policy = str(source.get("license_policy") or "unknown").lower()
    if policy in AUTHORIZED_POLICIES:
        return True, "authorized:" + policy
    hint = str(source.get("license_hint") or "unknown").lower()
    if policy in {"permissive_only", "public_permissive", "public_safe"}:
        return hint in PERMISSIVE_HINTS or any(item in hint for item in PERMISSIVE_HINTS), "public_safe:" + hint
    if hint in BLOCKED_HINTS or any(item in hint for item in BLOCKED_HINTS):
        return False, "blocked:" + hint
    return hint in PERMISSIVE_HINTS, "hint:" + hint


def ensure_source(source: dict[str, Any], target_root: str | Path, fetch: bool = True) -> dict[str, Any]:
    allowed, reason = source_allowed(source)
    if not allowed:
        return {"ok": False, "skipped": True, "reason": reason, "source": source}
    local_path = source.get("path")
    if local_path:
        path = Path(str(local_path)).resolve()
        return {"ok": path.exists(), "path": str(path), "action": "local", "reason": reason, "source": source}
    if not fetch:
        return {"ok": False, "skipped": True, "reason": "fetch_disabled", "source": source}
    url = str(source.get("url") or "")
    if not url:
        return {"ok": False, "skipped": True, "reason": "missing_url", "source": source}
    branch = str(source.get("branch") or "main")
    target = Path(target_root) / safe_name(str(source.get("name") or url))
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and (target / ".git").exists():
        subprocess.run(["git", "fetch", "--depth", "1", "origin", branch], cwd=str(target), check=True)
        subprocess.run(["git", "checkout", branch], cwd=str(target), check=True)
        subprocess.run(["git", "reset", "--hard", "FETCH_HEAD"], cwd=str(target), check=True)
        action = "updated"
    else:
        subprocess.run(["git", "clone", "--depth", "1", "--branch", branch, url, str(target)], check=True)
        action = "cloned"
    return {"ok": True, "path": str(target.resolve()), "action": action, "reason": reason, "source": source}


def commit_sha(path: str | Path) -> str:
    repo = Path(path)
    if not (repo / ".git").exists():
        return ""
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(repo), text=True).strip()
    except Exception:
        return ""


def rights_record(source: dict[str, Any], decision: str) -> dict[str, Any]:
    source_uri = str(source.get("url") or source.get("path") or source.get("name") or "local")
    rights_id = str(source.get("rights_id") or stable_id("rights_code_", source_uri))
    policy = str(source.get("license_policy") or "unknown")
    authorized = policy.lower() in AUTHORIZED_POLICIES
    return {
        "rights_id": rights_id,
        "provider_name": source.get("provider_name") or source.get("owner") or source.get("name") or "Authorized Code Source",
        "provider_type": source.get("provider_type") or ("owner" if authorized else "public_source"),
        "agreement_id": source.get("agreement_id") or stable_id("agreement_", source_uri + "|" + policy),
        "agreement_uri": source.get("agreement_uri") or "urn:ailovanta:authorization:" + rights_id,
        "source_uri": source_uri,
        "source_type": source.get("source_type") or "github_repo",
        "license_name": source.get("license_name") or source.get("license_hint") or policy,
        "allowed_uses": source.get("allowed_uses") or ["finetune", "distillation", "evaluation", "commercial_runtime"],
        "allowed_model_types": source.get("allowed_model_types") or ["ailovanta-code"],
        "allowed_training_types": source.get("allowed_training_types") or DEFAULT_TRAINING_TYPES,
        "commercial_use_allowed": bool(source.get("commercial_use_allowed", authorized)),
        "distillation_allowed": bool(source.get("distillation_allowed", True)),
        "redistribution_allowed": bool(source.get("redistribution_allowed", False)),
        "expires_at": source.get("expires_at"),
        "status": source.get("rights_status") or "active",
        "authorization_basis": decision,
        "scope_note": source.get("scope_note") or ("authorized unrestricted private/code learning source" if authorized else "public safe code source"),
    }


def ingest_sources(
    sources_path: str | Path,
    target_root: str | Path = "runtime_data/source_repos",
    corpus_output: str | Path = "runtime_data/code_corpus_github.jsonl",
    rights_path: str | Path = "runtime_data/rights_proofs.json",
    jobs_path: str | Path = "runtime_data/code_training_jobs.json",
    fetch: bool = True,
    create_job: bool = False,
    training_kind: str = "code_lora",
    max_file_bytes: int = 512_000,
    corpus_mode: str = "instructions",
) -> dict[str, Any]:
    if corpus_mode not in {"instructions", "code", "mixed"}:
        raise ValueError("corpus_mode must be one of: instructions, code, mixed")
    sources = load_sources(sources_path)
    rights = RightsProofRegistry(rights_path)
    jobs = CodeTrainingJobStore(jobs_path, rights_registry=rights)
    output = Path(corpus_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    source_results: list[dict[str, Any]] = []
    total_records = 0
    total_bytes = 0
    languages: set[str] = set()
    created_jobs: list[dict[str, Any]] = []
    with output.open("w", encoding="utf-8") as out:
        for source in sources:
            ensured = ensure_source(source, target_root=target_root, fetch=fetch)
            if not ensured.get("ok"):
                source_results.append(ensured)
                continue
            path = Path(str(ensured["path"]))
            decision = str(ensured.get("reason") or "")
            record = rights.add_rights(rights_record(source, decision))
            sha = commit_sha(path)
            code_records = build_records(path, max_file_bytes=max_file_bytes) if corpus_mode in {"code", "mixed"} else []
            code_stats = last_stats() if corpus_mode in {"code", "mixed"} else {}
            instruction_records = build_instruction_records(path, max_file_bytes=max_file_bytes) if corpus_mode in {"instructions", "mixed"} else []
            instruction_stats = instruction_last_stats() if corpus_mode in {"instructions", "mixed"} else {}
            records = [*instruction_records, *code_records]
            for item in records:
                body = dict(item.__dict__)
                body.update(
                    {
                        "training_record_kind": "instruction" if "instruction" in body else "code",
                        "source_url": source.get("url") or source.get("path"),
                        "source_name": source.get("name") or safe_name(str(source.get("url") or path)),
                        "commit_sha": sha,
                        "rights_id": record["rights_id"],
                        "license_policy": source.get("license_policy"),
                        "authorization_basis": decision,
                    }
                )
                out.write(json.dumps(body, ensure_ascii=False, sort_keys=True) + "\n")
                total_records += 1
                total_bytes += int(body.get("bytes") or 0)
                languages.add(str(body.get("language") or "unknown"))
            job = None
            if create_job and records:
                dataset_id = stable_id("dataset_code_", str(output.resolve()) + "|" + record["rights_id"] + "|" + corpus_mode)
                job = jobs.create_job(rights_id=record["rights_id"], dataset_id=dataset_id, kind=training_kind)
                created_jobs.append(job)
            source_results.append({**ensured, "rights_id": record["rights_id"], "records": len(records), "code_records": len(code_records), "instruction_records": len(instruction_records), "code_stats": code_stats, "instruction_stats": instruction_stats, "job_id": job.get("job_id") if job else None})
    return {
        "ok": total_records > 0,
        "schema_version": "ailovanta.github_code_ingest.v1",
        "sources": len(sources),
        "accepted_sources": len([item for item in source_results if item.get("ok")]),
        "records": total_records,
        "bytes": total_bytes,
        "languages": sorted(languages),
        "corpus_output": str(output),
        "rights_path": str(rights.path),
        "jobs_path": str(jobs.path),
        "created_jobs": created_jobs,
        "corpus_mode": corpus_mode,
        "results": source_results,
    }
