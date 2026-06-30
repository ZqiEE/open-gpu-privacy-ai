# Training Jobs

v1.13 extends training jobs with a public/core bridge export and local pipeline runner.

Training jobs start as public metadata records, then can be exported and run through `ailovanta-core`.

## Training job kinds

```text
rag_import
lora_micro
evaluation_batch
private_memory_tune
```

## Create a training job

```bash
curl -X POST http://127.0.0.1:8000/training/jobs \
  -H "Content-Type: application/json" \
  -d '{"kind":"rag_import","name":"demo-rag","dataset_uri":"file://local/docs","base_model":"ailovanta-bootstrap:local"}'
```

## Register a model version

```bash
curl -X POST http://127.0.0.1:8000/models/versions \
  -H "Content-Type: application/json" \
  -d '{"name":"ailovanta-v0.1-local","base_model":"ailovanta-bootstrap:local","source_job_id":"train_xxxxxxxx"}'
```

## Export one training job for core

API:

```bash
curl -X POST http://127.0.0.1:8000/training/jobs/train_xxxxxxxx/export
```

CLI:

```bash
python scripts/export_training_job.py train_xxxxxxxx --output-dir runtime_data/training_exports
```

The exported JSON uses:

```text
schema_version: ailovanta.training_job.v1
```

## Run the local training pipeline

CLI:

```bash
python scripts/run_training_pipeline.py train_xxxxxxxx --core-path ../ailovanta-core
```

API:

```text
POST /training/pipeline/run
```

Payload:

```json
{
  "job_id": "train_xxxxxxxx",
  "core_path": "../ailovanta-core",
  "work_dir": "runtime_data/training_pipeline"
}
```

Result:

```text
export_path
core_result
model_version
```

## Next steps

- Real RAG importer
- LoRA/QLoRA worker integration
- Model artifact paths
- Evaluation reports
- Version promotion rules
