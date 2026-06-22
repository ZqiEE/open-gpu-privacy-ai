from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import time

from api.content_addressing import hash_object


@dataclass
class ModelPackage:
    name: str
    version: str
    base: str
    package_hash: str
    adapter_hash: str
    data_hash: str
    score: float
    object_ref: str
    runtime: str
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: round(time(), 3))


def build_model_package(
    name: str,
    version: str,
    base: str,
    adapter_hash: str,
    data_hash: str,
    score: float,
    object_ref: str,
    runtime: str = "local-runtime",
    tags: list[str] | None = None,
) -> dict:
    payload = {
        "name": name,
        "version": version,
        "base": base,
        "adapter_hash": adapter_hash,
        "data_hash": data_hash,
        "score": score,
        "object_ref": object_ref,
        "runtime": runtime,
        "tags": tags or [],
    }
    package_hash = hash_object(payload)
    package = ModelPackage(
        name=name,
        version=version,
        base=base,
        package_hash=package_hash,
        adapter_hash=adapter_hash,
        data_hash=data_hash,
        score=score,
        object_ref=object_ref,
        runtime=runtime,
        tags=tags or [],
    )
    return asdict(package)
