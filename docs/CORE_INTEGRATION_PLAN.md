# Ailovanta Core Integration Plan

## Goal

Connect the public `ailovanta` job lifecycle to `ailovanta-core` H-SwarmTrain Lite rounds through a stable interface.

## Current public flow

```text
POST /training/jobs
-> SchedulerStore records training job
-> GET /training/jobs lists training jobs
-> POST /models/versions registers model version metadata
```

## Current core flow

```text
TrainingGoal
-> LiteScheduler
-> TaskDispatcher
-> WorkerRegistry
-> DemoWorker
-> LiteValidator
-> LiteAggregator
-> RoundSummaryBuilder
-> RunAudit
```

## Required runtime flow

Storage is not enough. Ailovanta also needs model execution and request routing.

```text
User request
-> Access Router
-> Runtime Pool selection
-> model manifest lookup
-> local cache check
-> missing chunk fetch
-> hash verification
-> model load / adapter load
-> inference or training task
-> result validation
-> usage, score, reputation record
```

The public repository should not assume one central server runs all model requests.

## Bridge interface

The public repository should export a training job payload shaped like:

```json
{
  "job_id": "train_xxx",
  "kind": "lora_micro",
  "base_model": "qwen2.5:3b",
  "dataset_uri": "file://demo/docs",
  "max_steps": 100,
  "notes": "local demo"
}
```

Ailovanta Core should accept it as a `TrainingGoal` plus machine profile list.

## Runtime pool interface

The public repository should also prepare a runtime request shape:

```json
{
  "request_id": "req_xxx",
  "model_id": "ailovanta-base-001",
  "version": "1.0.0",
  "privacy_level": "public",
  "task_type": "chat_completion",
  "latency_target_ms": 2000,
  "max_price": 0.01,
  "region_hint": "auto"
}
```

The runtime router should return:

```json
{
  "runtime_id": "runtime_xxx",
  "node_id": "node_gpu_01",
  "cache_state": "warm",
  "model_manifest_hash": "sha256:...",
  "estimated_latency_ms": 900,
  "verification_required": true
}
```

## Phase 1: local bridge

- Add a public script that exports training jobs as JSON.
- Add a core script that imports one public training job JSON.
- Convert public training job to `TrainingGoal`.
- Run one H-SwarmTrain Lite round.
- Write round summary.
- Return model version metadata.

## Phase 2: runtime router MVP

- Add runtime capability records.
- Add model manifest records.
- Add cache state records.
- Route small models to local/small-GPU pools.
- Route large models to large-GPU warm pools.
- Route private models only to trusted runtime pools.

## Phase 3: controlled bridge

- Replace file handoff with API handoff.
- Add stable schema version.
- Add round result manifest.
- Add worker capability mapping.
- Add stronger validation result structure.
- Add runtime result records.

## Phase 4: testnet bridge

- Use controlled nodes only.
- Add node admission rules.
- Add task signing.
- Add artifact metadata registry.
- Add production dashboard metrics.
- Add cost and latency accounting.

## Do not do yet

- Do not expose core internals in the public repository.
- Do not run arbitrary code from public jobs.
- Do not claim real global distributed training before the bridge is tested.
- Do not route every model request to one central server.
