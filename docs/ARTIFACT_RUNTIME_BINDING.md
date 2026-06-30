# Artifact Runtime Binding

## Purpose

Artifact Runtime Binding connects a promoted foundation artifact to a runtime model key and backend reference.

This closes the gap between:

```text
foundation artifact
-> runtime model manifest
-> worker/runtime lookup
```

## What is stored

```text
model_key
model_id
version
runtime_manifest_hash
artifact_hash
artifact_id
checkpoint_uri
backend_kind
backend_ref
status
metadata
```

## API

```text
GET /artifact-bindings
GET /artifact-bindings/{binding_id}
GET /artifact-bindings/by-model/{model_key}
POST /artifact-bindings/{binding_id}/status
```

## Import integration

When a foundation result is imported:

```text
foundation result
-> core result
-> runtime model
-> artifact distribution metadata when local bytes are available
-> artifact binding
-> chain event with binding_id
```

The binding metadata may include:

```text
artifact_distribution
artifact_manifest
```

`artifact_distribution` records storage/chunk evidence. `artifact_manifest` is only attached when the storage bytes hash matches the model artifact hash, so validation does not confuse artifact identity with checkpoint file bytes.

## Worker integration

The worker resolves:

```text
model_id + version
-> model_key
-> latest artifact binding
```

The binding is returned in worker inference metadata. This does not claim the checkpoint is already a production-grade loaded model; it records which artifact the runtime model is bound to, so a real loader/backend can use the binding deterministically.

## Meaning

Ailovanta no longer has only a model label. It has a traceable connection:

```text
runtime model
-> artifact hash
-> checkpoint uri
-> backend ref
```
