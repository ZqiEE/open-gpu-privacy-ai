# Foundation Pipeline

## Purpose

This is the one-command bridge from public foundation jobs to core foundation artifacts and back into public runtime identity.

## Flow

```text
public foundation job
-> export job json
-> ailovanta-core foundation runner
-> foundation result json
-> import result
-> runtime model manifest
-> chain event
-> owned-chat route
```

## CLI

```bash
python scripts/run_foundation_pipeline.py foundation_job_xxx --core-path ../ailovanta-core
```

Optional output:

```bash
python scripts/run_foundation_pipeline.py foundation_job_xxx \
  --core-path ../ailovanta-core \
  --work-dir runtime_data/foundation_pipeline \
  --output runtime_data/foundation_pipeline/pipeline_result.json
```

## API

```text
POST /foundation/pipeline/run
```

Payload:

```json
{
  "job_id": "foundation_job_xxx",
  "core_path": "../ailovanta-core",
  "work_dir": "runtime_data/foundation_pipeline"
}
```

## Result

The pipeline returns:

```text
export_path
result_path
core_result
runtime_model
chain_event
```

## Meaning

This closes the current local foundation loop:

```text
create job
-> run core planner
-> register artifact-backed runtime model
-> append chain event
```

A real distributed checkpoint worker is still the next hard production layer.
