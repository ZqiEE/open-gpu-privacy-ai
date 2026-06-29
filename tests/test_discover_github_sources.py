from scripts.discover_github_sources import source_from_repo, upsert_sources


def test_source_from_repo_uses_authorized_policy() -> None:
    source = source_from_repo(
        {
            "full_name": "demo/example",
            "name": "example",
            "clone_url": "https://github.com/demo/example.git",
            "html_url": "https://github.com/demo/example",
            "default_branch": "main",
            "license": {"spdx_id": "NOASSERTION"},
            "stargazers_count": 1000,
            "language": "Python",
        },
        policy="authorized_unrestricted",
        authorization_basis="operator authorized",
    )

    assert source["license_policy"] == "authorized_unrestricted"
    assert source["authorization_basis"] == "operator authorized"
    assert source["commercial_use_allowed"] is True
    assert source["distillation_allowed"] is True


def test_upsert_sources_deduplicates_by_url() -> None:
    manifest = {"schema_version": "ailovanta.github_code_sources.v1", "sources": []}
    first = {"name": "repo", "url": "https://github.com/demo/repo.git", "stars": 1}
    second = {"name": "repo", "url": "https://github.com/demo/repo.git", "stars": 2}

    added_first = upsert_sources(manifest, [first])
    added_second = upsert_sources(manifest, [second])

    assert added_first == 1
    assert added_second == 0
    assert manifest["sources"][0]["stars"] == 2
