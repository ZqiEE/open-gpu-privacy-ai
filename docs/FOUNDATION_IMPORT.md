# Foundation Import

## Purpose

After core runs a foundation job, public must import the produced result and make it usable.

## Flow

```text
result json
-> core result record
-> local artifact chunk manifest when backend_ref/checkpoint_uri is a file
-> replica book entry for storage_pool tracking
-> runtime model record
-> artifact binding
-> chain event
-> anchor receipt for the chain event
-> owned chat route
```

## CLI

```bash
python scripts/import_foundation_result.py runtime_data/foundation_result.json
```

## API module

```text
api.foundation_result_api
POST /foundation/results/import
```

## Import steps

```text
1. Register core result
2. Prepare artifact distribution metadata when a local file is available
3. Register runtime model
4. Register artifact binding
5. Append chain event
6. Anchor the chain event through the configured anchor adapter
```

## Artifact distribution

When `artifact.backend_ref` or `artifact.checkpoint_uri` points at a local file, import builds:

```text
runtime_data/artifact_manifests/<artifact_id>.manifest.json
runtime_data/replica_book.json
```

The chain event metadata records the distribution manifest hash and storage artifact hash.

If the replica policy requires more copies than currently exist, the artifact remains under-replicated until storage repair tasks complete:

```bash
python scripts/replica_repair.py plan --target-node storage-2
python scripts/replica_repair.py complete <task_id>
```

The import also anchors a compact promotion payload:

```text
event_id
event_hash
model_id/version
artifact_hash
runtime_manifest_hash
binding_id
```

The resulting `anchor_receipt` is stored in chain event metadata and the chain event is marked `anchored`. This is a Web3-style proof pointer; checkpoint/model bytes stay in artifact storage and distributed replicas.

Important: `artifact.artifact_hash` is the model artifact identity hash from core. The chunk manifest `artifact_hash` is the bytes hash of the stored checkpoint/model file. They are kept separate as:

```text
model_artifact_hash
storage_artifact_hash
```
