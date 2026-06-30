from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any, Callable

FRONTIER_SCHEMA = "ailovanta.github_source_frontier.v1"

LANGUAGE_QUERIES = [
    "language:Python",
    "language:TypeScript",
    "language:JavaScript",
    "language:Go",
    "language:Rust",
    "language:Java",
    "language:C++",
    "language:C",
    "language:C#",
    "language:Swift",
    "language:Kotlin",
    "language:Ruby",
    "language:PHP",
]

CODE_TOPIC_TERMS = [
    "compiler",
    "interpreter",
    "linter",
    "formatter",
    "testing",
    "framework",
    "sdk",
    "cli",
    "database",
    "distributed",
    "machine-learning",
    "agent",
]


def load_frontier(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return _initial_frontier()
    return json.loads(target.read_text(encoding="utf-8-sig"))


def save_frontier(path: str | Path, frontier: dict[str, Any]) -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(frontier, ensure_ascii=False, indent=2), encoding="utf-8")
    return frontier


def run_frontier_discovery(
    *,
    sources_path: str | Path,
    frontier_path: str | Path = "runtime_data/github_source_frontier.json",
    search_repositories: Callable[..., list[dict[str, Any]]],
    source_from_repo: Callable[[dict[str, Any], str, str], dict[str, Any]],
    upsert_sources: Callable[[dict[str, Any], list[dict[str, Any]]], int],
    load_manifest: Callable[[Path], dict[str, Any]],
    save_manifest: Callable[[Path, dict[str, Any]], None],
    token: str | None = None,
    max_queries: int = 5,
    pages: int = 1,
    per_page: int = 10,
    policy: str = "authorized_unrestricted",
    authorization_basis: str = "operator authorized autonomous GitHub source frontier",
) -> dict[str, Any]:
    frontier = load_frontier(frontier_path)
    now = round(time.time(), 3)
    queries = select_queries(frontier, max_queries=max_queries, now=now)
    manifest = load_manifest(Path(sources_path))
    discovered_sources: list[dict[str, Any]] = []
    query_results: list[dict[str, Any]] = []
    for query in queries:
        try:
            repos = search_repositories(query, pages=pages, per_page=per_page, token=token)
            query_results.append({"query": query, "ok": True, "repos": len(repos)})
        except Exception as exc:
            repos = []
            query_results.append({"query": query, "ok": False, "reason": type(exc).__name__, "message": str(exc)})
        record_query_result(frontier, query, repos, now=now)
        for repo in repos:
            source = source_from_repo(repo, policy, authorization_basis)
            source.update(source_metadata(repo, query, now))
            discovered_sources.append(source)
        expand_frontier(frontier, repos, now=now)
    added = upsert_sources(manifest, discovered_sources)
    manifest["sources"] = sorted(manifest.get("sources", []), key=lambda item: float(item.get("discovery_score") or 0), reverse=True)
    save_manifest(Path(sources_path), manifest)
    frontier["updated_at"] = now
    save_frontier(frontier_path, frontier)
    return {
        "ok": True,
        "schema_version": FRONTIER_SCHEMA,
        "frontier_path": str(frontier_path),
        "sources_path": str(sources_path),
        "queries": queries,
        "query_results": query_results,
        "discovered": len(discovered_sources),
        "added": added,
        "total_sources": len(manifest.get("sources", [])),
        "frontier_queries": len(frontier.get("queries", {})),
    }


def select_queries(frontier: dict[str, Any], max_queries: int, now: float | None = None) -> list[str]:
    timestamp = float(now if now is not None else time.time())
    ensure_seed_queries(frontier)
    rows = []
    for query, state in frontier.get("queries", {}).items():
        cooldown = int(state.get("cooldown_seconds") or 0)
        last_run = float(state.get("last_run_at") or 0)
        due = last_run <= 0 or timestamp - last_run >= cooldown
        if due and not state.get("disabled"):
            rows.append((float(state.get("priority") or 0), last_run, query))
    rows.sort(key=lambda item: (-item[0], item[1], item[2]))
    return [query for _, _, query in rows[:max_queries]]


def record_query_result(frontier: dict[str, Any], query: str, repos: list[dict[str, Any]], now: float | None = None) -> None:
    state = frontier.setdefault("queries", {}).setdefault(query, _query_state(query, priority=50))
    state["last_run_at"] = float(now if now is not None else time.time())
    state["runs"] = int(state.get("runs") or 0) + 1
    state["last_result_count"] = len(repos)
    state["total_result_count"] = int(state.get("total_result_count") or 0) + len(repos)
    if not repos:
        state["priority"] = max(1, float(state.get("priority") or 1) * 0.75)
        state["cooldown_seconds"] = min(86_400, int(state.get("cooldown_seconds") or 3600) * 2)
    else:
        state["priority"] = min(100, float(state.get("priority") or 1) + min(10, len(repos)))
        state["cooldown_seconds"] = int(state.get("cooldown_seconds") or 3600)


def expand_frontier(frontier: dict[str, Any], repos: list[dict[str, Any]], now: float | None = None) -> None:
    timestamp = float(now if now is not None else time.time())
    queries = frontier.setdefault("queries", {})
    for repo in repos:
        language = str(repo.get("language") or "").strip()
        if language:
            add_query(queries, f"stars:>=50 language:{language} archived:false", priority=55, now=timestamp)
        for topic in repo.get("topics") or []:
            topic_text = str(topic).strip().lower()
            if topic_text and any(term in topic_text for term in CODE_TOPIC_TERMS):
                add_query(queries, f"stars:>=25 topic:{topic_text} archived:false", priority=45, now=timestamp)


def add_query(queries: dict[str, Any], query: str, priority: float, now: float | None = None) -> None:
    existing = queries.get(query)
    if existing:
        existing["priority"] = max(float(existing.get("priority") or 0), priority)
        return
    state = _query_state(query, priority=priority)
    state["discovered_at"] = float(now if now is not None else time.time())
    queries[query] = state


def source_metadata(repo: dict[str, Any], query: str, now: float) -> dict[str, Any]:
    score = discovery_score(repo)
    return {
        "discovered_by_query": query,
        "discovered_at": now,
        "last_seen_at": now,
        "discovery_score": score,
        "forks": repo.get("forks_count"),
        "open_issues": repo.get("open_issues_count"),
        "pushed_at": repo.get("pushed_at"),
        "topics": repo.get("topics") or [],
    }


def discovery_score(repo: dict[str, Any]) -> float:
    stars = float(repo.get("stargazers_count") or 0)
    forks = float(repo.get("forks_count") or 0)
    issues = float(repo.get("open_issues_count") or 0)
    size = float(repo.get("size") or 0)
    score = math.log10(stars + 10) * 35 + math.log10(forks + 10) * 15
    if repo.get("language"):
        score += 10
    if repo.get("license"):
        score += 8
    if repo.get("archived"):
        score -= 50
    if repo.get("disabled"):
        score -= 50
    if size > 0:
        score += min(12, math.log10(size + 10) * 2)
    score -= min(12, math.log10(issues + 10) * 2)
    return round(max(0, score), 3)


def ensure_seed_queries(frontier: dict[str, Any]) -> None:
    queries = frontier.setdefault("queries", {})
    for index, language in enumerate(LANGUAGE_QUERIES):
        add_query(queries, f"stars:>=500 {language} archived:false", priority=100 - index)
    for index, term in enumerate(CODE_TOPIC_TERMS[:6]):
        add_query(queries, f"stars:>=100 topic:{term} archived:false", priority=70 - index)


def _initial_frontier() -> dict[str, Any]:
    frontier = {"schema_version": FRONTIER_SCHEMA, "queries": {}, "created_at": round(time.time(), 3)}
    ensure_seed_queries(frontier)
    return frontier


def _query_state(query: str, priority: float) -> dict[str, Any]:
    return {"query": query, "priority": priority, "cooldown_seconds": 3600, "runs": 0}
