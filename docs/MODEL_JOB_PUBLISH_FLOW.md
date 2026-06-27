# Model Job Publish Flow

This flow connects local model training output to the decentralized trust path.

It replaces this manual gap:

```text
run_model_job -> local output directory -> manual catalog steps
```

with:

```text
run_model_job
-> zip output directory
-> /artifacts/store
-> signed receipt
-> /catalog/from-receipt
-> validate
-> notarize
-> publish
-> readiness check
```

## Start API

```bash
export AILOVANTA_CHAIN_ANCHOR=http
export AILOVANTA_CHAIN_ANCHOR_URI=http://127.0.0.1:8000/notary/mock/anchor
export AILOVANTA_NODE_SECRETS_JSON='{"demo-node":"demo-secret"}'
uvicorn api.main_code:app --host 0.0.0.0 --port 8000 --reload
```

## Run local model job and publish

```bash
python scripts/run_model_job_publish_flow.py \
  --payload runtime_data/payload.json \
  --source-id train_demo_001 \
  --node-id demo-node \
  --node-secret demo-secret
```

With GPU flag:

```bash
python scripts/run_model_job_publish_flow.py \
  --payload runtime_data/payload.json \
  --source-id train_demo_001 \
  --node-id demo-node \
  --node-secret demo-secret \
  --gpu
```

## Output

The script prints:

```text
job_result
bundle
artifact
receipt
cataloged
validated
notarized
published
readiness
```

## Production replacement

In production, replace local demo pieces with:

```text
AILOVANTA_ARTIFACT_STORE=s3 | r2 | minio | external
AILOVANTA_CHAIN_ANCHOR=notary | external | http
real node id / node secret registry
real GPU output directory
```

Postgres and Redis remain index/queue only. The publish trust path is artifact URI, artifact hash, receipt, anchor receipt, manifest.
