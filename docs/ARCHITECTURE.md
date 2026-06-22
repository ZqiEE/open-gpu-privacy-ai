# Architecture

## Product Flywheel

1. Free private AI attracts users
2. Users run local nodes to unlock free access
3. Nodes contribute idle GPU/CPU
4. Compute supply grows
5. Inference and training costs go down
6. More users and builders join the network

## System Layers

```text
User App
  - Private AI Chat
  - Open Work Mode
  - Ephemeral Records
  - Private Memory

Node Client
  - Device Detection
  - Resource Limit
  - Worker Runtime
  - Heartbeat

Scheduler
  - Node Scoring
  - Task Dispatch
  - Retry
  - Verification
  - SQLite Persistence

AI Runtime
  - Ollama
  - Qwen/Llama
  - Local Memory
  - Fallback Reply

Training Layer
  - RAG Import
  - Data Cleaning
  - Evaluation Batch
  - LoRA/QLoRA Micro Jobs
  - Model Version Registry
```

## First Realistic Workloads

Consumer computers are unstable and heterogeneous. The first tasks should be short, verifiable, and easy to retry.

- inference
- image generation
- data cleaning
- evaluation
- RAG import
- LoRA/QLoRA micro jobs
- private memory tuning
