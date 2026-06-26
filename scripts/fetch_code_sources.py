from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse

TRUSTED_POLICY = {"owner_controlled", "explicit_permission", "internal"}
GOOD_HINTS = {"mit", "apache", "apache-2.0", "bsd", "bsd-2-clause", "bsd-3-clause", "isc", "mpl", "mpl-2.0", "unlicense", "cc0"}
BAD_HINTS = {"gpl", "lgpl", "agpl", "sspl", "unknown"}


def safe_name(value: str) -> str:
    parsed = urlparse(value)
    raw = Path(parsed.path).name or value
    raw = raw.removesuffix(".git")
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in raw)[:80]


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def hint_from_file(root: Path) -> str:
    names = {"license", "license.md", "license.txt", "copying", "copying.txt"}
    for child in root.iterdir() if root.exists() and root.is_dir() else []:
        if child.name.lower() not in names or not child.is_file():
            continue
        text = child.read_text(encoding="utf-8", errors="ignore")[:8000].lower()
        if "apache license" in text and "version 2.0" in text:
            return "apache-2.0"
        if "mit license" in text or "permission is hereby granted" in text:
            return "mit"
        if "mozilla public license" in text:
            return "mpl-2.0"
        if "isc license" in text:
            return "isc"
        if "the unlicense" in text:
            return "unlicense"
        if "affero general public license" in text:
            return "agpl"
        if "lesser general public license" in text:
            return "lgpl"
        if "gnu general public license" in text:
            return "gpl"
        if "redistribution and use" in text:
            return "bsd"
        return "license_file_present"
    return "unknown"


def allowed(source: dict, repo_path: Path | None = None) -> tuple[bool, str]:
    policy = str(source.get("license_policy") or "unknown").lower()
    if policy in TRUSTED_POLICY:
        return True, policy
    hint = str(source.get("license_hint") or "unknown").lower()
    if repo_path is not None and hint == "unknown":
        hint = hint_from_file(repo_path)
    if policy in {"permissive_only", "public_permissive"}:
        return (hint in GOOD_HINTS or any(item in hint for item in GOOD_HINTS), "hint:" + hint)
    if hint in BAD_HINTS or any(item in hint for item in BAD_HINTS):
        return False, "blocked:" + hint
    return hint in GOOD_HINTS, "hint:" + hint


def fetch_source(source: dict, target_root: Path) -> dict:
    if not source.get("enabled", True):
        return {"name": source.get("name"), "enabled": False, "skipped": True}
    pre_ok, pre_reason = allowed(source)
    if not pre_ok and source.get("license_policy") not in {"permissive_only", "public_permissive"}:
        return {"name": source.get("name"), "url": source.get("url"), "skipped": True, "reason": pre_reason}
    url = source["url"]
    branch = source.get("branch") or "main"
    name = source.get("name") or safe_name(url)
    target = target_root / safe_name(str(name))
    target_root.mkdir(parents=True, exist_ok=True)
    if target.exists() and (target / ".git").exists():
        run(["git", "fetch", "--depth", "1", "origin", branch], cwd=target)
        run(["git", "checkout", branch], cwd=target)
        run(["git", "reset", "--hard", "FETCH_HEAD"], cwd=target)
        action = "updated"
    else:
        run(["git", "clone", "--depth", "1", "--branch", branch, url, str(target)])
        action = "cloned"
    post_ok, post_reason = allowed(source, target)
    if not post_ok:
        return {"name": name, "url": url, "branch": branch, "path": str(target), "action": action, "skipped": True, "reason": post_reason}
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(target), text=True).strip()
    return {"name": name, "url": url, "branch": branch, "path": str(target), "commit": commit, "action": action, "license_policy": source.get("license_policy", "unknown"), "license_decision": post_reason}


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch approved GitHub code sources")
    p.add_argument("--sources", default="runtime_data/github_code_sources.json")
    p.add_argument("--target-root", default="runtime_data/source_repos")
    args = p.parse_args()
    source_path = Path(args.sources)
    if not source_path.exists():
        example = Path("runtime_data.example/github_code_sources.json")
        raise SystemExit(f"sources file not found: {source_path}. Copy {example} first.")
    config = json.loads(source_path.read_text(encoding="utf-8"))
    results = [fetch_source(item, Path(args.target_root)) for item in config.get("sources", [])]
    print(json.dumps({"count": len(results), "fetched": len([r for r in results if not r.get("skipped")]), "skipped": len([r for r in results if r.get("skipped")]), "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
