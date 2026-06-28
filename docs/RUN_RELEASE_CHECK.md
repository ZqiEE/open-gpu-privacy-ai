# Run Release Check

The repo now has a GitHub Actions workflow:

```text
.github/workflows/release-check.yml
```

It runs:

```text
python validate.py
python -m pytest -q
python scripts/check_release.py --route-key owned-chat/default --verify-bytes
```

Manual run:

```text
GitHub -> Actions -> Release Check -> Run workflow
```

The workflow uploads:

```text
release-gate-report
```

Open `release_gate.json` from the artifact and inspect:

```text
stage
blockers
checks
```

Expected current state is likely `release_blocked` until real core path, active route, node secrets, backup snapshot, runtime node, artifact store, and anchor are available in the runner.

Do not treat the project as ready until the workflow returns:

```text
stage = release_pass
```
