from __future__ import annotations

import csv
import io
import subprocess
from typing import Any


def detect_gpu() -> dict[str, Any]:
    """Best-effort local GPU probe.

    The project must not pretend GPU training is active. This probe reports what
    the local machine can actually expose through CUDA/torch or nvidia-smi.
    """

    torch_info = detect_torch_cuda()
    smi_info = detect_nvidia_smi()
    primary = smi_info or torch_info
    return {
        "has_gpu": bool(primary.get("has_gpu")),
        "gpu_name": primary.get("gpu_name"),
        "gpu_memory_gb": primary.get("gpu_memory_gb", 0.0),
        "available_gpu_memory_gb": primary.get("available_gpu_memory_gb", 0.0),
        "cuda_available": bool(torch_info.get("cuda_available")),
        "torch_device_count": int(torch_info.get("torch_device_count", 0)),
        "nvidia_smi_available": bool(smi_info.get("nvidia_smi_available")),
        "utilization_percent": primary.get("utilization_percent"),
        "probe_source": primary.get("probe_source", "none"),
    }


def detect_torch_cuda() -> dict[str, Any]:
    try:
        import torch  # type: ignore
    except Exception:
        return {"has_gpu": False, "cuda_available": False, "torch_device_count": 0, "probe_source": "torch-unavailable"}

    cuda_available = bool(torch.cuda.is_available())
    device_count = int(torch.cuda.device_count()) if cuda_available else 0
    if not cuda_available or device_count < 1:
        return {"has_gpu": False, "cuda_available": cuda_available, "torch_device_count": device_count, "probe_source": "torch"}

    props = torch.cuda.get_device_properties(0)
    total_gb = round(float(props.total_memory) / (1024**3), 2)
    free_gb = 0.0
    try:
        free_bytes, _total_bytes = torch.cuda.mem_get_info(0)
        free_gb = round(float(free_bytes) / (1024**3), 2)
    except Exception:
        free_gb = total_gb

    return {
        "has_gpu": True,
        "gpu_name": torch.cuda.get_device_name(0),
        "gpu_memory_gb": total_gb,
        "available_gpu_memory_gb": free_gb,
        "cuda_available": True,
        "torch_device_count": device_count,
        "probe_source": "torch",
    }


def detect_nvidia_smi() -> dict[str, Any]:
    command = [
        "nvidia-smi",
        "--query-gpu=name,memory.total,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=10)
    except Exception:
        return {"has_gpu": False, "nvidia_smi_available": False, "probe_source": "nvidia-smi-unavailable"}

    rows = list(csv.reader(io.StringIO(completed.stdout.strip())))
    if not rows:
        return {"has_gpu": False, "nvidia_smi_available": True, "probe_source": "nvidia-smi"}

    first = [part.strip() for part in rows[0]]
    name = first[0] if len(first) > 0 else None
    total_mb = parse_float(first[1]) if len(first) > 1 else 0.0
    free_mb = parse_float(first[2]) if len(first) > 2 else 0.0
    utilization = parse_float(first[3]) if len(first) > 3 else None
    return {
        "has_gpu": bool(name),
        "gpu_name": name,
        "gpu_memory_gb": round(total_mb / 1024, 2) if total_mb else 0.0,
        "available_gpu_memory_gb": round(free_mb / 1024, 2) if free_mb else 0.0,
        "utilization_percent": utilization,
        "nvidia_smi_available": True,
        "probe_source": "nvidia-smi",
    }


def parse_float(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0
