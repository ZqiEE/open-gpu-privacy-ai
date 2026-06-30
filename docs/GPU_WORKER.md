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
continuous real training: next stage, requires real training jobs and model backend execution
```

This distinction matters: Ailovanta should not claim a fully self-trained foundation model until GPU jobs produce real checkpoints and those checkpoints are promoted into runtime bindings.
