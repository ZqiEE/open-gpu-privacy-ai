from __future__ import annotations

from dataclasses import dataclass

import psutil


@dataclass
class ResourceLimits:
    max_cpu_percent: int = 60
    min_free_memory_gb: float = 1.5


class ResourceGuard:
    def __init__(self, limits: ResourceLimits | None = None) -> None:
        self.limits = limits or ResourceLimits()

    def can_run_job(self) -> tuple[bool, str]:
        cpu = psutil.cpu_percent(interval=0.2)
        free_gb = psutil.virtual_memory().available / (1024**3)
        if cpu > self.limits.max_cpu_percent:
            return False, f"cpu too high: {cpu:.1f}% > {self.limits.max_cpu_percent}%"
        if free_gb < self.limits.min_free_memory_gb:
            return False, f"free memory too low: {free_gb:.2f}GB < {self.limits.min_free_memory_gb}GB"
        return True, "ok"
