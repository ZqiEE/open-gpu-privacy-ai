# Trust Flow Demo

This demo proves the decentralized artifact path without treating the API server as the final source of truth.

## Start API

Local demo anchor:

```bash
export AILOVANTA_CHAIN_ANCHOR=http
export AILOVANTA_CHAIN_ANCHOR_URI=http://127.0.0.1:8000/notary/mock/anchor
uvicorn api.main_code:app --host 0.0.0.0 --port 8000 --reload
```

Strict worker proof mode:

```bash
export AILOVANTA_NODE_SECRETS_JSON='{"demo-node":"demo-secret"}'
```

## Run full trust flow

Loose demo mode:

```bash
python scripts/demo_trust_flow.py
```

Strict receipt verification:

```bash
python scripts/demo_trust_flow.py --require-valid
```

## What it does

```text
create local demo artifact
-> /artifacts/store
-> signed worker receipt
-> /catalog/from-receipt
-> /catalog/items/{id}/validate
-> /catalog/items/{id}/notarize
-> /catalog/items/{id}/publish
-> /runtime/local/load
-> /runtime/local/generate
```

## Trust objects

The server indexes metadata, but the trust path is:

```text
artifact_uri
artifact_hash
worker receipt
anchor_receipt
runtime manifest
```

## Production replacements

Replace demo adapters with durable systems:

```text
AILOVANTA_ARTIFACT_STORE=s3 | r2 | minio | external
AILOVANTA_ARTIFACT_STORE_URI=s3://bucket/prefix
AILOVANTA_CHAIN_ANCHOR=notary | external | http
AILOVANTA_CHAIN_ANCHOR_URI=https://your-notary-or-chain-gateway/anchor
AILOVANTA_CONTENT_GATEWAY=https://ipfs.io/ipfs
```

Postgres and Redis are coordination/index layers only.
