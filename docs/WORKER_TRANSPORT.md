# Worker Transport

## Purpose

This is the next step after runtime routing.

```text
owned chat request
-> runtime router selects Ailovanta runtime manifest
-> worker transport calls selected worker
-> worker returns answer
```

## Worker endpoint

A worker must expose:

```text
POST /v1/owned/infer
```

Request fields:

```text
prompt
model_id
version
policy_mode
runtime_id
node_id
model_manifest_hash
```

Response fields:

```text
answer
source
model_id
version
runtime_id
node_id
model_manifest_hash
artifact_binding
validation_provenance
```

## Configure worker URL

Register runtime endpoint:

```text
POST /runtime/endpoints
```

Payload:

```json
{
  "runtime_id": "rt-owned-1",
  "url": "http://127.0.0.1:9001"
}
```

Runtime-specific URL:

```bash
export AILOVANTA_WORKER_URL_RT_OWNED_1=http://127.0.0.1:9001
```

Default URL:

```bash
export AILOVANTA_DEFAULT_WORKER_URL=http://127.0.0.1:9001
```

## Run demo worker

```bash
uvicorn api.demo_worker_app:app --port 9001 --reload
```

## Run owned app

```bash
uvicorn api.main_owned:app --reload
```

## Boundary

Owned runtime no longer returns a placeholder after routing. It now attempts worker inference. If no worker URL is configured or the worker is not reachable, owned chat returns not ready instead of using the bootstrap model.

When `AILOVANTA_REQUIRE_OWNED_MODEL=true`, `/ailovanta/v1/chat` uses this owned runtime path and does not silently fall back to the bootstrap runtime.

## Worker result validation

After a worker returns `/v1/owned/infer`, the result can be converted into a validation receipt:

```text
POST /worker-results/validate
```

The receipt checks:

```text
worker result answer is non-empty
node_id/runtime_id are present
model_manifest_hash matches artifact_binding.runtime_manifest_hash
artifact_manifest.artifact_hash matches artifact_binding.artifact_hash
sampled chunks contain sha256 hashes and replica/source provenance
```

Validation receipts are stored locally and can optionally create a reputation event:

```text
event_type: worker_result_validation
delta: +1.0 when passed, -3.0 when failed
```

Receipts can be listed with:

```text
GET /worker-results/validations
GET /worker-results/validations?node_id=<node>
```
