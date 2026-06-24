# Ailovanta Model Backend Boundary

## Current truth

Ailovanta does not yet ship a production Ailovanta-owned foundation model.

The public MVP currently uses a local bootstrap inference path:

```text
/app or API request
-> Ailovanta FastAPI
-> local Ollama adapter
-> configured local bootstrap model
-> Ailovanta response wrapper, conversation store, usage, runtime metadata
```

This is a development bridge so the product can be tested before the core training and runtime promotion loop is complete.

## What it is not

```text
Not Alibaba Cloud.
Not DashScope.
Not a completed Ailovanta-owned foundation model.
Not proof of global distributed GPU training.
```

If `OLLAMA_MODEL` is set to a third-party open model, that model is only the bootstrap local runtime. It should not be described as the final Ailovanta model.

## Target path

The intended Ailovanta-owned model path is:

```text
public training job
-> core bridge export
-> ailovanta-core H-SwarmTrain Lite round
-> validation and aggregation
-> training artifact metadata
-> model version registration
-> runtime model manifest
-> trusted runtime pool
-> chat/run request routed to verified Ailovanta runtime
```

## Product rule

Keep the public product honest:

```text
First: local bootstrap runtime.
Next: public/core bridge.
Then: verified training artifacts.
Then: Ailovanta-owned runtime manifests.
Finally: distributed inference and training claims.
```

## Next engineering step

Build the Phase 1 file bridge from `docs/CORE_INTEGRATION_PLAN.md`:

1. Export one public training job as versioned JSON.
2. Import that JSON in `ailovanta-core`.
3. Convert it into a `TrainingGoal`.
4. Run one local H-SwarmTrain Lite round.
5. Export a result manifest back to the public shape.
