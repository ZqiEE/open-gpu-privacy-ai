# Local GPU Worker

## Purpose

Ailovanta's target is continuous owned training: authorized data becomes verified training tasks, tasks are assigned to distributed nodes, GPU workers produce candidate artifacts, validators check results, and promoted artifacts become runtime-bound model versions.

The current local app does not automatically use your GPU just because the chat UI is open. The API server and the training worker are separate processes:

```text
API/app process
-> serves app, dashboard, API docs, owned runtime routing

GPU worker process
-> detects local GPU
-> registers the machine as a node
-> pulls training jobs
-> submits signed/verified results
```

## Windows

Start the API first:

```powershell
.\start_ailovanta_windows.bat
```

Then open a second PowerShell window and start the local training worker:

```powershell
.\start_training_worker_windows.bat
```

If the API chose a non-default port, pass it explicitly:

```powershell
.\start_training_worker_windows.bat -Server http://127.0.0.1:8001
```

Seed a real local training job:

```powershell
.\seed_training_job_windows.bat
```

If the API is on port 8001:

```powershell
.\seed_training_job_windows.bat -Server http://127.0.0.1:8001
```

The seeded job writes a JSONL dataset into `runtime_data/local_training_seed.jsonl` and queues a `lora_micro` job. The worker then trains a real local artifact:

```text
runtime_data/models/<job-name>-<version>/ngram_model.json
runtime_data/models/<job-name>-<version>/output.json
```

If Transformers/CUDA/PEFT are installed and the job requests them, `api.model_job` can run a Transformers/LoRA path. Otherwise it still performs real local lightweight n-gram training over the dataset instead of writing a fake success file.

After a local training artifact is produced, the worker binds it to `ailovanta-owned:candidate` so owned chat can route through the latest training artifact instead of the bootstrap checkpoint. If you already trained before this binding step existed, bind the newest local artifact manually:

```powershell
.\.venv\Scripts\python.exe scripts\bind_latest_training_artifact.py
```

Restart the API after code changes. The bootstrap launcher will not overwrite an existing active training artifact binding.

## GPU Status

Check local GPU detection:

```powershell
.\.venv\Scripts\python.exe scripts\show_gpu.py
```

Or through the API:

```text
GET /local/gpu
```

The response reports whether CUDA or `nvidia-smi` is visible, the detected GPU name, total GPU memory, available GPU memory, utilization, and probe source.

## Distributed Training Meaning

One running worker means one contributing node. If more users run workers, the scheduler can assign more data, training, validation, and runtime tasks across those nodes.

Current status:

```text
owned runtime route: implemented
artifact binding/provenance: implemented
local GPU worker registration: implemented
real local lightweight training artifact: implemented
CUDA/QLoRA training backend: supported when optional dependencies and CUDA torch are installed
continuous distributed training: next stage, requires many external workers and promotion automation
```

This distinction matters: Ailovanta should not claim a fully self-trained foundation model until GPU jobs produce real checkpoints and those checkpoints are promoted into runtime bindings.
