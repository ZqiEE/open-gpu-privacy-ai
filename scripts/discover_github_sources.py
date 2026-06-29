from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.github_code_ingest import safe_name

DEFAULT_QUERIES = [
    "stars:>=500 language:Python archived:false",
    "stars:>=500 language:TypeScript archived:false",
    "stars:>=500 language:JavaScript archived:false",
    "stars:>=300 language:Go archived:false",
    "stars:>=300 language:Rust archived:false",
]


def load_manifest(path: Path) -> dict:
    if not path.exists():
        return {"schema_version": "ailovanta.github_code_sources.v1", "sources": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def github_get(url: str, token: str | None = None) -> dict:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Ailovanta-GitHub-Discovery"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = Request(url, headers=headers)
    with urlopen(req, timeout=60) as res:
        return json.loads(res.read().decode("utf-8"))


def search_repositories(query: str, pages: int, per_page: int, token: str | None = None) -> list[dict]:
    repos: list[dict] = []
    for page in range(1, pages + 1):
        params = urlencode({"q": query, "sort": "stars", "order": "desc", "per_page": per_page, "page": page})
        data = github_get("https://api.github.com/search/repositories?" + params, token=token)
        repos.extend(data.get("items") or [])
    return repos


def source_from_repo(repo: dict, policy: str, authorization_basis: str) -> dict:
    license_info = repo.get("license") if isinstance(repo.get("license"), dict) else {}
    return {
        "name": safe_name(str(repo.get("full_name") or repo.get("name") or repo.get("clone_url"))),
        "url": repo.get("clone_url") or repo.get("html_url"),
        "html_url": repo.get("html_url"),
        "branch": repo.get("default_branch") or "main",
        "license_policy": policy,
        "license_hint": license_info.get("spdx_id") or "unknown",
        "authorization_basis": authorization_basis,
        "source_type": "github_repo",
        "stars": repo.get("stargazers_count"),
        "language": repo.get("language"),
        "allowed_training_types": ["code_lora", "code_qlora", "code_distill", "code_eval"],
        "allowed_uses": ["finetune", "distillation", "evaluation", "commercial_runtime"],
        "commercial_use_allowed": True,
        "distillation_allowed": True,
        "enabled": True,
    }


def upsert_sources(manifest: dict, sources: list[dict]) -> int:
    items = manifest.setdefault("sources", [])
    seen = {item.get("url"): item for item in items}
    added = 0
    for source in sources:
        url = source.get("url")
        if not url:
            continue
        if url in seen:
            seen[url].update(source)
        else:
            items.append(source)
            seen[url] = source
            added += 1
    return added


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover broad GitHub repository sources and write an Ailovanta source manifest")
    parser.add_argument("--output", default="runtime_data/github_code_sources.json")
    parser.add_argument("--query", action="append", default=[])
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--per-page", type=int, default=50)
    parser.add_argument("--policy", default="authorized_unrestricted")
    parser.add_argument("--authorization-basis", default="operator asserts authorization for broad GitHub code learning")
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    args = parser.parse_args()
    token = os.getenv(args.token_env)
    queries = args.query or DEFAULT_QUERIES
    manifest = load_manifest(Path(args.output))
    discovered: list[dict] = []
    for query in queries:
        repos = search_repositories(query, pages=args.pages, per_page=args.per_page, token=token)
        discovered.extend(source_from_repo(repo, args.policy, args.authorization_basis) for repo in repos)
    added = upsert_sources(manifest, discovered)
    save_manifest(Path(args.output), manifest)
    print(json.dumps({"ok": True, "output": args.output, "queries": queries, "discovered": len(discovered), "added": added, "total_sources": len(manifest.get("sources", []))}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
