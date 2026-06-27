from __future__ import annotations

import importlib.util
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
