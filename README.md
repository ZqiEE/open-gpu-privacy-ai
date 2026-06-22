# Open GPU Privacy AI MVP

> Run a node, use private AI for free. No node, use paid mode.  
> 开节点，免费用隐私 AI；不开节点，付费用。

A local static MVP for a **user-owned GPU network for private AI**. The product uses free access to attract users, lets users contribute idle GPU/CPU through local nodes, and turns user growth into compute growth.

## v0.2 Update

This version is English-first for global users, developers, and investors. Chinese is kept as supporting copy.

### What changed

- English-first homepage and README
- More polished global product positioning
- New compute network dashboard
- Better access gate: contributor mode vs paid mode
- Training simulator upgraded with job size and node tier logic
- Investor narrative page
- Robot-ready memory positioning

## Core Positioning

**The user-owned GPU network for private AI.**

Users contribute local compute. The network gets lower-cost AI inference, fine-tuning, evaluation, and data processing capacity. Contributors unlock free AI usage. Non-contributors can use paid mode.

## MVP Features

- Contributor mode: run a GPU/CPU node and use AI for free
- Paid mode: use AI without running a node
- Node share slider, device score, trust score, task simulation
- Private AI chat demo
- Standard / Open / Creative / Private Companion modes
- Ephemeral prompts, replies, chat records, and robot memory
- Local robot memory with one-click wipe
- Compute network dashboard
- Training engine simulation: RAG, data cleaning, LoRA/QLoRA, task dispatch, model merge
- Investor narrative: user growth → compute growth → lower cost → better AI → more users

## Run Locally

Double click:

```text
index.html
```

Or run:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

## Roadmap

1. Add Ollama + Qwen/Llama local inference
2. Add Stable Diffusion worker
3. Build Python/Rust node client
4. Build FastAPI scheduler
5. Add PostgreSQL node/user system
6. Add robot SDK and local-first memory

## Product Keywords

**Free, private, open, user-owned, robot-ready AI.**

**免费、隐私、开放、共建、机器人。**
