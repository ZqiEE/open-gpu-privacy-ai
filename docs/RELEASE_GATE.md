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
  --verify-bytes \
  --verify-distribution \
  --verify-chain
```

Run through API:

```text
POST /ops/release/gate
{
  "core_path": "../ailovanta-core",
  "result_path": "runtime_data/local_loop/foundation_result.json",
  "route_key": "owned-chat/default",
  "run_tests": false,
  "verify_bytes": true,
  "verify_distribution": true,
  "verify_chain": true
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

`verify_bytes` checks artifact byte integrity. `verify_distribution` checks the owned model's distributed storage evidence: `artifact_distribution`, chunk manifest hash, replica book entry, and replica health.

`verify_chain` checks the owned model's promotion proof: chain registry event, event hash, anchor status, chain transaction/anchor URI, and anchor receipt. It does not put model bytes on-chain.

Do not deploy publicly unless the stage is `release_pass`.
