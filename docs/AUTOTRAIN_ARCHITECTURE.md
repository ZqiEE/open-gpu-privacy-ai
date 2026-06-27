# AutoTrain Architecture

Ailovanta AutoTrain turns authorized data into distributed training jobs and runtime-ready model candidates.

## Responsibilities

AutoTrain is responsible for:

```text
discover trainable data
-> check Rights Proof Registry
-> build dataset pack
-> create training job
-> split tasks
-> assign distributed nodes
-> collect worker results
-> validate outputs
-> aggregate candidate updates
-> create candidate model version
-> pass promotion gate
-> publish runtime manifest
```

## Required default

Every training job created by AutoTrain must include:

```text
distributed_required=true
```

Local execution is allowed only as a controlled distributed simulation. The public API and core importer must still treat the task as distributed.

## Node classes

- CPU nodes: data cleaning, license checks, repository parsing, deduplication, benchmark building.
- Small GPU nodes: embedding, teacher sampling, code explanation generation, small adapter jobs.
- Strong GPU nodes: QLoRA, LoRA, adapter training, batch inference, candidate model update.
- Validator nodes: pytest, lint, typecheck, sandbox execution, benchmark scoring.
- Aggregator: merges candidate results and computes promotion metrics.
- Runtime nodes: load model manifests, keep warm caches, serve Ailovanta-Code responses.

## Promotion

A model candidate can become runtime-visible only after validation and promotion gate checks pass. Failing candidates remain audit records and must not be presented as active production models.
