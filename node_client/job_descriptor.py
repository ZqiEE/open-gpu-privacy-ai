from __future__ import annotations

from dataclasses import dataclass


DESCRIPTOR_FIELDS = {"schema_version", "source", "owner"}


@dataclass(frozen=True)
class DescriptorCheck:
    ok: bool
    reason: str
    descriptor: dict


class JobDescriptorPolicy:
    def __init__(self, required: bool = False) -> None:
        self.required = required

    def validate(self, job: dict) -> DescriptorCheck:
        payload = job.get("payload", {})
        descriptor = job.get("descriptor") or payload.get("descriptor") or {}
        if not descriptor:
            if self.required:
                return DescriptorCheck(False, "missing descriptor", {})
            return DescriptorCheck(True, "descriptor optional", {})
        missing = sorted(DESCRIPTOR_FIELDS - set(descriptor.keys()))
        if missing:
            return DescriptorCheck(False, "missing descriptor fields: " + ",".join(missing), descriptor)
        return DescriptorCheck(True, "descriptor accepted", descriptor)
