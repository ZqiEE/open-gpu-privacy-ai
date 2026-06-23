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

## Phase 1: local bridge

- Add a public script that exports training jobs as JSON.
- Add a core script that imports one public training job JSON.
- Convert public training job to `TrainingGoal`.
- Run one H-SwarmTrain Lite round.
- Write round summary.
- Return model version metadata.

## Phase 2: controlled bridge

- Replace file handoff with API handoff.
- Add stable schema version.
- Add round result manifest.
- Add worker capability mapping.
- Add stronger validation result structure.

## Phase 3: testnet bridge

- Use controlled nodes only.
- Add node admission rules.
- Add task signing.
- Add artifact metadata registry.
- Add production dashboard metrics.

## Do not do yet

- Do not expose core internals in the public repository.
- Do not run arbitrary code from public jobs.
- Do not claim real global distributed training before the bridge is tested.
