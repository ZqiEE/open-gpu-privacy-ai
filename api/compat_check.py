from __future__ import annotations

import importlib.util
from pathlib import Path
import platform
from typing import Any


def module_state(name: str) -> dict[str, Any]:
    spec = importlib.util.find_spec(name)
    return {"name": name, "installed": spec is not None}


def check_local_stack() -> dict[str, Any]:
    system = platform.system()
    result: dict[str, Any] = {
        "platform": platform.platform(),
        "system": system,
        "python": platform.python_version(),
        "modules": [module_state(name) for name in ["torch", "transformers", "datasets", "accelerate", "peft", "bitsandbytes"]],
        "cuda": {"available": False, "device_count": 0, "devices": []},
        "qlora_ready": False,
        "lora_ready": False,
        "recommendations": [],
    }
    try:
        import torch  # type: ignore

        result["torch"] = {"version": getattr(torch, "__version__", "unknown")}
        result["cuda"] = {
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            "devices": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())] if torch.cuda.is_available() else [],
        }
    except Exception as exc:
        result["torch_error"] = str(exc)

    installed = {item["name"]: item["installed"] for item in result["modules"]}
    result["lora_ready"] = bool(installed.get("torch") and installed.get("transformers") and installed.get("datasets") and installed.get("peft"))
    result["qlora_ready"] = bool(result["lora_ready"] and installed.get("bitsandbytes") and result["cuda"]["available"] and system == "Linux")

    if not installed.get("torch"):
        result["recommendations"].append("install torch before real local model runs")
    if not installed.get("transformers") or not installed.get("datasets"):
        result["recommendations"].append("install transformers and datasets for Trainer-based runs")
    if not installed.get("peft"):
        result["recommendations"].append("install peft for LoRA adapter runs")
    if not installed.get("bitsandbytes"):
        result["recommendations"].append("bitsandbytes missing; QLoRA 4-bit may fall back or fail on this system")
    if system == "Windows":
        result["recommendations"].append("Windows detected: use LoRA or WSL2/Linux for QLoRA; bitsandbytes is usually smoother on Linux + NVIDIA CUDA")
    if system != "Linux":
        result["recommendations"].append("QLoRA production path recommended on Linux with NVIDIA CUDA")
    if not result["cuda"]["available"]:
        result["recommendations"].append("CUDA GPU not detected; real training may be slow")
    return result


def check_real_training_requirements(payload: dict[str, Any], profile: dict[str, Any] | None = None) -> dict[str, Any]:
    stack = check_local_stack()
    installed = {item["name"]: item["installed"] for item in stack["modules"]}
    backend = training_backend_from_payload(payload)
    blockers: list[str] = []
    warnings: list[str] = []
    profile = profile or {}

    if not payload.get("real") and not payload.get("use_transformers") and not payload.get("peft") and not payload.get("qlora"):
        return {
            "ok": True,
            "real_training_required": False,
            "backend": "portable",
            "blockers": [],
            "warnings": ["job did not request a real Transformers/LoRA backend"],
            "stack": stack,
        }

    if payload.get("requires_gpu") and not profile.get("has_gpu"):
        blockers.append("gpu_required_but_node_has_no_gpu")
    if payload.get("requires_gpu") and not stack["cuda"]["available"]:
        blockers.append("cuda_required_but_torch_cuda_unavailable")

    for module in ("torch", "transformers", "datasets"):
        if not installed.get(module):
            blockers.append("missing_module:" + module)
    if backend in {"lora", "qlora"} and not installed.get("peft"):
        blockers.append("missing_module:peft")
    if backend == "qlora":
        if not installed.get("bitsandbytes"):
            blockers.append("missing_module:bitsandbytes")
        if stack["system"] != "Linux":
            blockers.append("qlora_requires_linux_cuda_runtime")
        if not stack["cuda"]["available"]:
            blockers.append("qlora_requires_cuda")

    base_model = str(payload.get("base_model") or "")
    if not base_model:
        blockers.append("missing_base_model")
    else:
        model_ref = classify_base_model_ref(base_model)
        if model_ref["kind"] == "local_missing":
            blockers.append("base_model_path_missing")
        elif model_ref["kind"] == "hf_or_remote":
            warnings.append("base_model_not_local_will_require_hf_cache_or_network")
    return {
        "ok": not blockers,
        "real_training_required": True,
        "backend": backend,
        "blockers": blockers,
        "warnings": warnings,
        "base_model": base_model,
        "base_model_ref": classify_base_model_ref(base_model) if base_model else None,
        "stack": stack,
    }


def training_backend_from_payload(payload: dict[str, Any]) -> str:
    if payload.get("qlora"):
        return "qlora"
    if payload.get("peft") or payload.get("lora"):
        return "lora"
    return "transformers"


def classify_base_model_ref(value: str) -> dict[str, Any]:
    path = Path(value)
    looks_path = value.startswith((".", "~", "file://")) or path.is_absolute() or (len(value) > 1 and value[1] == ":") or "\\" in value
    if looks_path:
        normalized = value.removeprefix("file://")
        local_path = Path(normalized)
        return {"kind": "local_ready" if local_path.exists() else "local_missing", "path": str(local_path)}
    return {"kind": "hf_or_remote", "ref": value}
