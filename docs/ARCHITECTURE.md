# Architecture

## Product Flywheel

1. 免费 AI 吸引用户
2. 用户为了免费使用而开启节点
3. 节点贡献闲置 GPU/CPU
4. 平台算力成本下降
5. AI 更便宜、更快、更个性化
6. 更多用户加入，形成网络效应

## System Layers

```text
User App
  - AI Chat
  - Open Mode
  - Ephemeral Records
  - Robot Memory

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

AI Runtime
  - Ollama
  - Qwen/Llama
  - Stable Diffusion
  - LoRA/QLoRA

Training Layer
  - RAG
  - Data Cleaning
  - Micro Fine-tuning
  - Federated Aggregation
```

## First Realistic Workloads

Consumer computers are unstable and heterogeneous. The first tasks should be short, verifiable, and easy to retry.

- inference
- image generation
- data cleaning
- evaluation
- LoRA/QLoRA
- personalized robot memory
