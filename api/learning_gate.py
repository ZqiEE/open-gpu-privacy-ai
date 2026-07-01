from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from api.foundation_job_export import export_foundation_job
from api.foundation_result_finalize import finalize_foundation_result_file
from api.foundation_result_import import import_foundation_result_file
from api.learning_foundation import create_job_from_latest_pack
from api.model_monitor import ModelMonitorStore
from api.model_warm import ModelWarm, WarmSpec
from api.owned_doctor import OwnedDoctor


def metric_score_from_result(result: dict[str, Any]) -> float:
    artifact = result.get("artifact") or {}
    metrics = artifact.get("metrics") or {}
    eval_loss = float(metrics.get("avg_eval_loss", metrics.get("eval_loss", 1.0)) or 1.0)
    accepted = float(metrics.get("accepted_checkpoints", 0.0) or 0.0)
    loss_score = max(0.0, min(1.0, 1.0 / (1.0 + max(0.0, eval_loss))))
    checkpoint_bonus = 0.1 if accepted > 0 else 0.0
    local_bonus = 0.05 if metrics.get("execution_mode") == "local" else 0.0
    return round(min(1.0, loss_score + checkpoint_bonus + local_bonus), 4)


def build_eval_payload(
    foundation_result: dict[str, Any],
    baseline_model: str = "ailovanta-owned:baseline",
    baseline_score: float = 0.45,
) -> dict[str, Any]:
    artifact = foundation_result.get("artifact") or {}
    model_id = artifact.get("model_id", "ailovanta-owned")
    version = artifact.get("version", "candidate")
    candidate_model = f"{model_id}:{version}"
    candidate_score = metric_score_from_result(foundation_result)
    metrics = artifact.get("metrics") or {}
    return {
        "candidate_model": candidate_model,
        "baseline_model": baseline_model,
        "metrics": [
            {"name": "autotruth_quality", "candidate_score": candidate_score, "baseline_score": baseline_score, "weight": 1.0},
            {"name": "artifact_integrity", "candidate_score": 1.0 if artifact.get("artifact_hash") else 0.0, "baseline_score": 0.9, "weight": 1.0},
            {"name": "checkpoint_execution", "candidate_score": 1.0 if metrics.get("execution_mode") == "local" else 0.6, "baseline_score": 0.6, "weight": 0.5},
        ],
        "regression_rate": 0.0 if candidate_score >= baseline_score else 0.1,
        "safety_fail_rate": 0.0,
    }


def run_core_eval_gate(core_root: Path, eval_payload: dict[str, Any], work_dir: Path) -> dict[str, Any]:
    eval_path = work_dir / "eval_payload.json"
    eval_path.write_text(json.dumps(eval_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    command = [sys.executable, str(core_root / "scripts" / "run_eval_gate.py"), str(eval_path)]
    proc = subprocess.run(command, cwd=core_root, check=True, text=True, capture_output=True)
    return json.loads(proc.stdout)


def build_foundation_command(
    core_root: Path,
    export_path: Path,
    result_path: Path,
    execute_checkpoints: bool = False,
    checkpoint_output_root: str | Path | None = None,
    training_command: str | None = None,
) -> list[str]:
    command = [sys.executable, str(core_root / "scripts" / "run_foundation_job.py"), str(export_path), "--output", str(result_path)]
    if execute_checkpoints:
        command.append("--execute-checkpoints")
    if checkpoint_output_root:
        command.extend(["--checkpoint-output-root", str(checkpoint_output_root)])
    if training_command:
        command.extend(["--training-command", training_command])
    return command


def build_backend_env(
    model_backend: str | None = None,
    base_model: str | None = None,
    backend_output_dir: str | Path | None = None,
    backend_device: str | None = None,
    backend_max_steps: int | None = None,
    backend_lr: float | None = None,
) -> dict[str, str]:
    env: dict[str, str] = {}
    if model_backend:
        env["AILOVANTA_MODEL_BACKEND"] = model_backend
    if base_model:
        env["AILOVANTA_BASE_MODEL"] = base_model
    if backend_output_dir:
        env["AILOVANTA_BACKEND_OUTPUT_DIR"] = str(backend_output_dir)
    if backend_device:
        env["AILOVANTA_BACKEND_DEVICE"] = backend_device
    if backend_max_steps is not None:
        env["AILOVANTA_BACKEND_MAX_STEPS"] = str(backend_max_steps)
    if backend_lr is not None:
        env["AILOVANTA_BACKEND_LR"] = str(backend_lr)
    return env


def prepare_runtime_after_import(model_key: str, enabled: bool = True, runtime_id: str = "rt-owned-1", node_id: str = "node-owned-1", gpu_memory_gb: float = 24.0) -> dict[str, Any]:
    before = OwnedDoctor().check(model_key)
    action = None
    after = before
    if enabled:
        action = ModelWarm().run(WarmSpec(model_key=model_key, runtime_id=runtime_id, node_id=node_id, gpu_memory_gb=gpu_memory_gb))
        after = OwnedDoctor().check(model_key)
    return {"enabled": enabled, "before": before, "action": action, "after": after}


def run_guarded_learning_pipeline(
    core_path: str | Path | None = None,
    work_dir: str | Path = "runtime_data/guarded_learning_pipeline",
    baseline_model: str = "ailovanta-owned:baseline",
    baseline_score: float = 0.45,
    allow_shadow_import: bool = False,
    execute_checkpoints: bool = False,
    checkpoint_output_root: str | Path | None = None,
    training_command: str | None = None,
    model_backend: str | None = None,
    base_model: str | None = None,
    backend_output_dir: str | Path | None = None,
    backend_device: str | None = None,
    backend_max_steps: int | None = None,
    backend_lr: float | None = None,
    prepare_runtime: bool = True,
    runtime_id: str = "rt-owned-1",
    node_id: str = "node-owned-1",
    runtime_gpu_memory_gb: float = 24.0,
    **job_kwargs: Any,
) -> dict[str, Any]:
    core_root = Path(core_path or os.getenv("AILOVANTA_CORE_PATH", "../ailovanta-core")).resolve()
    if not core_root.exists():
        raise ValueError("ailovanta-core path not found: " + str(core_root))

    output_root = Path(work_dir)
    exports_dir = output_root / "exports"
    results_dir = output_root / "results"
    gate_dir = output_root / "gate"
    for path in [exports_dir, results_dir, gate_dir]:
        path.mkdir(parents=True, exist_ok=True)

    job = create_job_from_latest_pack(**job_kwargs)
    job_id = job["job_id"]
    exported = export_foundation_job(job_id, exports_dir)
    export_path = Path(exported["export_path"]).resolve()
    result_path = (results_dir / f"{job_id}_foundation_result.json").resolve()
    checkpoint_root = checkpoint_output_root or (output_root / "checkpoints")
    backend_env = build_backend_env(
        model_backend=model_backend,
        base_model=base_model,
        backend_output_dir=backend_output_dir or (output_root / "model_backend"),
        backend_device=backend_device,
        backend_max_steps=backend_max_steps,
        backend_lr=backend_lr,
    )
    proc_env = os.environ.copy()
    proc_env.update(backend_env)

    subprocess.run(
        build_foundation_command(
            core_root,
            export_path,
            result_path,
            execute_checkpoints=execute_checkpoints,
            checkpoint_output_root=checkpoint_root if execute_checkpoints else None,
            training_command=training_command,
        ),
        cwd=core_root,
        env=proc_env,
        check=True,
    )

    foundation_result = finalize_foundation_result_file(result_path, write=True)
    eval_payload = build_eval_payload(foundation_result, baseline_model=baseline_model, baseline_score=baseline_score)
    gate_result = run_core_eval_gate(core_root, eval_payload, gate_dir)
    decision = (gate_result.get("decision") or {}).get("decision")

    artifact = foundation_result.get("artifact") or {}
    monitor = ModelMonitorStore()
    shadow = None
    if decision in {"promote", "shadow"}:
        shadow = monitor.register_shadow(
            candidate_model=eval_payload["candidate_model"],
            baseline_model=baseline_model,
            artifact_hash=artifact.get("artifact_hash"),
            metadata={"job_id": job_id, "decision": decision, "result_path": str(result_path), "execute_checkpoints": execute_checkpoints, "backend_env": backend_env, "finalized_by": artifact.get("metadata", {}).get("finalized_by")},
        )
        monitor.record_metric(
            eval_payload["candidate_model"],
            {item["name"]: float(item["candidate_score"]) for item in eval_payload["metrics"]},
            mode="shadow",
            metadata={"shadow_id": shadow["shadow_id"], "job_id": job_id, "execute_checkpoints": execute_checkpoints, "backend_env": backend_env},
        )

    imported = None
    live = None
    if decision == "promote":
        imported = import_foundation_result_file(result_path)
        if shadow:
            live = monitor.promote_live(shadow["shadow_id"])
    elif decision == "shadow" and allow_shadow_import:
        imported = import_foundation_result_file(result_path)

    model_key = eval_payload["candidate_model"]
    runtime_prepare = prepare_runtime_after_import(model_key, enabled=bool(imported) and prepare_runtime, runtime_id=runtime_id, node_id=node_id, gpu_memory_gb=runtime_gpu_memory_gb)

    return {
        "ok": True,
        "job": job,
        "export_path": str(export_path),
        "result_path": str(result_path),
        "execute_checkpoints": execute_checkpoints,
        "checkpoint_output_root": str(checkpoint_root) if execute_checkpoints else None,
        "backend_env": backend_env,
        "finalized_result": foundation_result,
        "eval_payload": eval_payload,
        "gate": gate_result,
        "shadow": shadow,
        "live": live,
        "imported": imported,
        "runtime_updated": imported is not None,
        "runtime_prepare": runtime_prepare,
    }
