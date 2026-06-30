import json
from pathlib import Path

from api.github_source_frontier import discovery_score, run_frontier_discovery, select_queries
from scripts.discover_github_sources import load_manifest, save_manifest, source_from_repo, upsert_sources


def _repo(name: str, language: str, stars: int, topics: list[str] | None = None) -> dict:
    return {
        "full_name": "demo/" + name,
        "name": name,
        "clone_url": f"https://github.com/demo/{name}.git",
        "html_url": f"https://github.com/demo/{name}",
        "default_branch": "main",
        "license": {"spdx_id": "MIT"},
        "stargazers_count": stars,
        "forks_count": 30,
        "open_issues_count": 5,
        "size": 1200,
        "language": language,
        "topics": topics or [],
        "archived": False,
    }


def test_frontier_selects_seed_queries() -> None:
    frontier = {"schema_version": "ailovanta.github_source_frontier.v1", "queries": {}}

    selected = select_queries(frontier, max_queries=3, now=1000)

    assert len(selected) == 3
    assert selected[0].startswith("stars:>=500 language:Python")


def test_frontier_discovery_persists_sources_and_expands_queries(tmp_path: Path) -> None:
    calls = []

    def fake_search(query: str, pages: int, per_page: int, token: str | None = None):
        calls.append(query)
        if "Python" in query:
            return [_repo("compiler-kit", "Python", 900, ["compiler", "testing"])]
        return []

    result = run_frontier_discovery(
        sources_path=tmp_path / "sources.json",
        frontier_path=tmp_path / "frontier.json",
        search_repositories=fake_search,
        source_from_repo=source_from_repo,
        upsert_sources=upsert_sources,
        load_manifest=load_manifest,
        save_manifest=save_manifest,
        max_queries=1,
        pages=1,
        per_page=10,
    )

    assert result["ok"] is True
    assert result["added"] == 1
    assert calls == ["stars:>=500 language:Python archived:false"]
    sources = json.loads((tmp_path / "sources.json").read_text(encoding="utf-8"))["sources"]
    assert sources[0]["name"] == "compiler-kit"
    assert sources[0]["discovery_score"] > 0
    frontier = json.loads((tmp_path / "frontier.json").read_text(encoding="utf-8"))
    assert "stars:>=50 language:Python archived:false" in frontier["queries"]
    assert "stars:>=25 topic:compiler archived:false" in frontier["queries"]


def test_discovery_score_penalizes_archived_repo() -> None:
    active = _repo("active", "Rust", 500)
    archived = {**active, "archived": True}

    assert discovery_score(active) > discovery_score(archived)
