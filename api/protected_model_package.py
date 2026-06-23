from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import time

from api.content_addressing import hash_object


@dataclass
class ProtectedModelPackage:
    package_hash: str
    protected_ref: str
    policy_hash: str
    access_level: str
    cipher_suite: str
    object_ref: str
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: round(time(), 3))


def build_protected_package(package: dict, access_level: str, policy: dict, object_ref: str, cipher_suite: str = "aes256-gcm-envelope", tags: list[str] | None = None) -> dict:
    policy_hash = hash_object(policy)
    protected_payload = {
        "package_hash": package["package_hash"],
        "access_level": access_level,
        "policy_hash": policy_hash,
        "object_ref": object_ref,
        "cipher_suite": cipher_suite,
    }
    protected = ProtectedModelPackage(
        package_hash=package["package_hash"],
        protected_ref="protected_" + hash_object(protected_payload)[:24],
        policy_hash=policy_hash,
        access_level=access_level,
        cipher_suite=cipher_suite,
        object_ref=object_ref,
        tags=tags or package.get("tags", []),
    )
    return asdict(protected)
