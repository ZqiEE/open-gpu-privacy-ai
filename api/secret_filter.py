from __future__ import annotations

import re
from dataclasses import dataclass

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}")),
    ("openai_key", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("google_api_key", re.compile(r"AIza[0-9A-Za-z_-]{20,}")),
    ("private_key", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("generic_secret_assignment", re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{12,}['\"]")),
]

HIGH_ENTROPY = re.compile(r"[A-Za-z0-9_\-+/=]{48,}")


@dataclass(frozen=True)
class SecretScanResult:
    ok: bool
    reasons: list[str]


def scan_text(text: str) -> SecretScanResult:
    reasons: list[str] = []
    sample = text[:1_000_000]
    for name, pattern in SECRET_PATTERNS:
        if pattern.search(sample):
            reasons.append(name)
    if looks_like_high_entropy_secret(sample):
        reasons.append("high_entropy_blob")
    return SecretScanResult(ok=not reasons, reasons=sorted(set(reasons)))


def looks_like_high_entropy_secret(text: str) -> bool:
    hits = 0
    for match in HIGH_ENTROPY.finditer(text):
        value = match.group(0)
        if len(set(value)) >= 18:
            hits += 1
        if hits >= 3:
            return True
    return False
