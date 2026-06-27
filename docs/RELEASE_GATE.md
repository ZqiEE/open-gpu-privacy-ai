# Release Gate

Use the release-ready app entry:

```bash
uvicorn api.main_release_ready:app --host 0.0.0.0 --port 8000
```

Run locally:

```bash
python scripts/check_release.py \
  --core-path ../ailovanta-core \
  --result runtime_data/local_loop/foundation_result.json \
  --route-key owned-chat/default \
  --verify-bytes
```

Run through API:

```text
POST /ops/release/gate
{
  "core_path": "../ailovanta-core",
  "result_path": "runtime_data/local_loop/foundation_result.json",
  "route_key": "owned-chat/default",
  "run_tests": false,
  "verify_bytes": true
}
```

The gate returns:

```text
stage = release_pass
stage = release_blocked
```

Release gate includes:

```text
validate.py
preflight
optional pytest
prod_ready_plus
route_health
runtime_route
alert summary
incident dry-run
```

Do not deploy publicly unless the stage is `release_pass`.
