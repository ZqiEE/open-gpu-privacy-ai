# Artifact Bound Runtime

## Purpose

Artifact Bound Runtime is the worker-side loader for artifact bindings.

It tries to resolve:

```text
model_id + version
-> artifact binding
-> backend_ref
-> local checkpoint or transformers model directory
-> worker response
```

## Supported binding kinds

```text
checkpoint-artifact    reads local checkpoint metadata when backend_ref is file:// or a local path
jsonl-stat             same as checkpoint-artifact for lightweight checkpoint outputs
transformers-local     loads a local Transformers model directory
transformers-causal-lm loads a local Transformers model directory
```

## Worker order

```text
1. artifact-bound runtime
2. fail closed when no active binding exists
3. optional bootstrap fallback only when AILOVANTA_WORKER_ALLOW_BOOTSTRAP_FALLBACK=true
```

The worker is strict by default. `/v1/owned/infer` must resolve an active or candidate artifact binding for `model_id + version`.

The request `model_manifest_hash` must match the binding `runtime_manifest_hash`. A mismatch returns `409` with `reason: model_manifest_hash_mismatch`.

When no binding exists, the worker returns `503` with `reason: missing_artifact_binding` instead of silently using Ollama. This keeps owned-runtime responses tied to imported training artifacts and prevents a bootstrap runtime from being presented as a verified owned model.

## Backend ref import rule

Public import prefers:

```text
artifact.backend_ref
```

and only falls back to:

```text
artifact.checkpoint_uri
```

The selected backend ref is stored in:

```text
artifact binding backend_ref
chain event metadata backend_ref
```

## Runtime ref readiness

On foundation result import, public checks whether the selected backend ref is locally reachable.

```text
ready -> binding remains active/candidate and runtime model remains active
not ready -> binding status becomes unavailable and runtime model status becomes unavailable
```

The chain event metadata records:

```text
ref_ready
ref_reason
runtime_status_update
```

Manual check endpoint:

```text
POST /artifact-bindings/{binding_id}/check
```

The check endpoint rechecks the local ref, updates the binding status, and updates the runtime model status. If a missing file appears later, the status can recover from `unavailable` to `candidate`.

Owned-chat also checks the active artifact binding before it calls the worker. If the active binding points to a missing local file or directory, owned-chat fails fast with `owned-runtime-unavailable` instead of silently falling through to a fallback runtime.

## Rollback sync

Rollback executor updates both:

```text
runtime model status
artifact binding status
```

So a rolled-back candidate is no longer selected by active binding lookup.

## Important reality

A jsonl-stat checkpoint is not a full conversational model. When the binding points to a lightweight checkpoint, the worker returns checkpoint-bound status and metadata instead of pretending to generate as a large model.

A real generative path requires a binding whose `backend_kind` is `transformers-local` or `transformers-causal-lm` and whose `backend_ref` points to a valid local model directory.

## Example binding

```json
{
  "model_key": "ailovanta-owned:candidate",
  "artifact_hash": "sha256:...",
  "checkpoint_uri": "file:///path/to/checkpoint.bin",
  "backend_kind": "checkpoint-artifact",
  "backend_ref": "file:///path/to/checkpoint.bin",
  "status": "active"
}
```

## Meaning

Owned chat can now be artifact-aware and fail closed. It calls a worker only after route selection, and the worker must prove the selected runtime manifest is the one bound to the local artifact. Rollback removes bad bindings from the active path, and import/check mark unreachable local refs and runtime manifests as unavailable.
