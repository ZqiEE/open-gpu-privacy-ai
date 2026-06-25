from __future__ import annotations

import ctypes
import os
import subprocess
from dataclasses import dataclass
from typing import Callable

import psutil


@dataclass
class GpuSample:
    utilization_percent: float | None = None
    memory_used_mb: float | None = None
    memory_total_mb: float | None = None
    temperature_c: float | None = None

    @property
    def memory_percent(self) -> float | None:
        if not self.memory_used_mb or not self.memory_total_mb:
            return None
        if self.memory_total_mb <= 0:
            return None
        return round((self.memory_used_mb / self.memory_total_mb) * 100, 2)


@dataclass
class ResourceSnapshot:
    cpu_percent: float
    free_memory_gb: float
    idle_seconds: float | None = None
    on_battery: bool | None = None
    gpu: GpuSample | None = None


@dataclass
class ResourceLimits:
    max_cpu_percent: int = 60
    min_free_memory_gb: float = 1.5
    max_gpu_percent: int = 80
    max_gpu_memory_percent: int = 80
    max_gpu_temperature_c: int = 78
    min_idle_seconds: int = 0
    pause_on_battery: bool = True


class ResourceGuard:
    def __init__(self, limits: ResourceLimits | None = None, snapshot_provider: Callable[[], ResourceSnapshot] | None = None) -> None:
        self.limits = limits or ResourceLimits()
        self.snapshot_provider = snapshot_provider or collect_snapshot

    def can_run_job(self) -> tuple[bool, str]:
        snap = self.snapshot_provider()
        if self.limits.pause_on_battery and snap.on_battery is True:
            return False, "on battery power"
        if snap.idle_seconds is not None and snap.idle_seconds < self.limits.min_idle_seconds:
            return False, f"user active: idle {snap.idle_seconds:.0f}s < {self.limits.min_idle_seconds}s"
        if snap.cpu_percent > self.limits.max_cpu_percent:
            return False, f"cpu too high: {snap.cpu_percent:.1f}% > {self.limits.max_cpu_percent}%"
        if snap.free_memory_gb < self.limits.min_free_memory_gb:
            return False, f"free memory too low: {snap.free_memory_gb:.2f}GB < {self.limits.min_free_memory_gb}GB"
        if snap.gpu:
            if snap.gpu.utilization_percent is not None and snap.gpu.utilization_percent > self.limits.max_gpu_percent:
                return False, f"gpu too busy: {snap.gpu.utilization_percent:.1f}% > {self.limits.max_gpu_percent}%"
            memory_percent = snap.gpu.memory_percent
            if memory_percent is not None and memory_percent > self.limits.max_gpu_memory_percent:
                return False, f"gpu memory too high: {memory_percent:.1f}% > {self.limits.max_gpu_memory_percent}%"
            if snap.gpu.temperature_c is not None and snap.gpu.temperature_c > self.limits.max_gpu_temperature_c:
                return False, f"gpu temperature too high: {snap.gpu.temperature_c:.1f}C > {self.limits.max_gpu_temperature_c}C"
        return True, "ok"

    def should_pause(self) -> bool:
        return not self.can_run_job()[0]


def collect_snapshot() -> ResourceSnapshot:
    cpu = psutil.cpu_percent(interval=0.2)
    free_gb = psutil.virtual_memory().available / (1024**3)
    return ResourceSnapshot(cpu_percent=cpu, free_memory_gb=free_gb, idle_seconds=detect_idle_seconds(), on_battery=detect_on_battery(), gpu=detect_gpu_sample())


def detect_on_battery() -> bool | None:
    try:
        battery = psutil.sensors_battery()
    except Exception:
        return None
    if battery is None:
        return None
    return not bool(battery.power_plugged)


def detect_idle_seconds() -> float | None:
    if os.name != "nt":
        return None
    try:
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

        info = LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):  # type: ignore[attr-defined]
            return None
        elapsed_ms = ctypes.windll.kernel32.GetTickCount() - info.dwTime  # type: ignore[attr-defined]
        return max(float(elapsed_ms) / 1000.0, 0.0)
    except Exception:
        return None


def detect_gpu_sample() -> GpuSample | None:
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except Exception:
        return None
    return parse_nvidia_smi(completed.stdout)


def parse_nvidia_smi(output: str) -> GpuSample | None:
    samples: list[GpuSample] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 4:
            continue
        sample = GpuSample(
            utilization_percent=_to_float(parts[0]),
            memory_used_mb=_to_float(parts[1]),
            memory_total_mb=_to_float(parts[2]),
            temperature_c=_to_float(parts[3]),
        )
        samples.append(sample)
    if not samples:
        return None
    return GpuSample(
        utilization_percent=_max_or_none(sample.utilization_percent for sample in samples),
        memory_used_mb=_max_or_none(sample.memory_used_mb for sample in samples),
        memory_total_mb=_max_or_none(sample.memory_total_mb for sample in samples),
        temperature_c=_max_or_none(sample.temperature_c for sample in samples),
    )


def _to_float(value: str) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _max_or_none(values) -> float | None:
    clean = [value for value in values if value is not None]
    return max(clean) if clean else None
