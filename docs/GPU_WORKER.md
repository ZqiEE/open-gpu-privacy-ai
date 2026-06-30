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

Recommended one-command full-auto mode:

```powershell
.\start_full_auto_windows.bat
```

This starts:

```text
API/app server
autonomous GitHub/source discovery and training queue
local GPU/CPU worker
owned runtime bootstrap and artifact binding
training artifact chunk manifest and replica book registration
replica maintenance loop for under-replicated artifact chunks
```

Check state:

```powershell
.\.venv\Scripts\python.exe scripts\show_full_auto_status.py
```

Stop all full-auto child processes:

```powershell
.\stop_full_auto_windows.bat
```

Manual mode is still available for debugging. Start the API first:

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

Automatically discover sources and queue a real local training job:

```powershell
.\start_auto_training_windows.bat
```

If the API is on port 8001:

```powershell
.\start_auto_training_windows.bat -Server http://127.0.0.1:8001
```

Run it as a continuous loop:

```powershell
.\start_auto_training_windows.bat -Server http://127.0.0.1:8001 -Loop
```

The automatic job discovers GitHub sources through a persistent frontier, writes/updates `runtime_data/github_code_sources.json`, fetches a bounded source set, builds `runtime_data/autonomous_source_training/autonomous_training_dataset.jsonl`, and queues a `lora_micro` job. The worker then trains a real local artifact:

```text
runtime_data/github_source_frontier.json
runtime_data/github_code_sources.json
runtime_data/continuous_training_ledger.json
```

`github_source_frontier.json` is the autonomous crawler state. It chooses due GitHub queries, expands new queries from languages/topics found in results, and scores sources. `github_code_sources.json` is the resulting source manifest/audit ledger, not a hand-written source list.

`continuous_training_ledger.json` is the training scheduler memory. It tracks source fingerprints, dataset hashes, job ids, and queued/done status so full-auto keeps moving to fresh code instead of repeatedly training the same batch.

```text
runtime_data/models/<job-name>-<version>/ngram_model.json
runtime_data/models/<job-name>-<version>/output.json
```

If Transformers/CUDA/PEFT are installed and the job requests them, `api.model_job` can run a Transformers/LoRA path. Otherwise it still performs real local lightweight n-gram training over the dataset instead of writing a fake success file.

The old `seed_training_job_windows.bat` command is only a deterministic smoke-test helper. Use `start_auto_training_windows.bat` for the real autonomous path.

After a local training artifact is produced, the worker first binds it to `ailovanta-owned:candidate` as a candidate. Owned chat can route through it only after the promotion gate marks the binding `active`. The binding also writes:

```text
runtime_data/artifact_manifests/<artifact_id>.manifest.json
runtime_data/replica_book.json
runtime_data/replica_repair_tasks.json
runtime_data/storage_replicas/
runtime_data/candidate_failure_actions.json
```

This is the local version of the distributed model storage plan: large model files are represented by chunk hashes, replica policy, replica locations, and runtime binding metadata. Runtime should load through the binding and manifest hash, not by handing out raw model files as public assets.

`start_full_auto_windows.bat` also starts `scripts/run_replica_maintenance.py --loop`. The maintenance loop scans for under-replicated chunks, creates `storage_replica_repair` tasks, copies locally reachable artifact chunks into `runtime_data/storage_replicas/`, verifies each chunk hash, and marks the task complete in `replica_book.json`.

Worker artifacts are registered as `candidate` first. The local promotion gate checks that the artifact is loadable, the training artifact has usable rows/transitions/loss, the dataset contains verifiable code records, code syntax checks pass, the backend can run an executable code-generation benchmark, artifact bytes match the binding hash, and the distributed replica book is healthy. Only a passing candidate is promoted to `active`; owned chat and runtime routes only use active bindings.

The executable code-generation benchmark is not a text-only label. For supported generative backends (`transformers-local` and `transformers-causal-lm`), the gate loads the local model directory from `backend_ref`, asks it to produce Python implementations for benchmark tasks, writes the result into `solution.py`, and runs `python -m pytest` against hidden task tests in a temporary sandbox. The candidate must meet the configured pass score before activation. Missing model paths, missing `torch`/`transformers`, failed tests, or non-generative backends keep the artifact in `candidate` and create retrain actions when appropriate.

If the gate fails, the failure is not just logged. Storage/replica blockers remain repair work for the replica maintenance loop. Model-quality/code-quality blockers such as invalid model output, too few rows/transitions, bad train loss, missing code records, syntax failures, unsupported code-generation backend, or artifact integrity failure create a `training_retrain` action in `runtime_data/candidate_failure_actions.json`. The worker submits queued retrain actions back to `/training/jobs` as `lora_micro` jobs using the same dataset lineage.

The built-in `lightweight-ngram` backend proves the local training, binding, storage, and gate pipeline, but it does not pass the executable code-generation gate. A candidate needs a real code-generation backend plus configured benchmark runner before it can become active.

If you already trained before this binding step existed, bind the newest local artifact manually:

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
local chunk manifest + replica book for trained artifacts: implemented
automatic local replica repair/maintenance: implemented
continuous source training ledger: implemented
training artifact promotion gate before active runtime: implemented
candidate failure action queue and auto retrain submission: implemented
code-record and syntax eval inside artifact promotion gate: implemented
executable pytest-backed code-generation benchmark gate: implemented
CUDA/QLoRA training backend: supported when optional dependencies and CUDA torch are installed
continuous distributed training: next stage, requires many external workers and promotion automation
```

This distinction matters: Ailovanta should not claim a fully self-trained foundation model until GPU jobs produce real checkpoints and those checkpoints are promoted into runtime bindings.
