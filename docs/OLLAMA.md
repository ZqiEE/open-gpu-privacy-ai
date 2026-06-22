# Ollama Local AI Runtime

v0.5 adds an optional Ollama adapter. The API tries to call Ollama first. If Ollama is not running, `/ai/chat` returns a safe local fallback reply so the runtime remains usable.

## Install Ollama

Install Ollama from the official app for your OS, then start it.

## Pull a model

Recommended small model for local testing:

```bash
ollama pull qwen2.5:3b
```

You can also use another local model:

```bash
ollama pull llama3.2:3b
```

## Configure model

Create a `.env` or export environment variables before starting the API:

```bash
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export OLLAMA_MODEL=qwen2.5:3b
export OLLAMA_TIMEOUT_SECONDS=30
```

Windows PowerShell:

```powershell
$env:OLLAMA_BASE_URL="http://127.0.0.1:11434"
$env:OLLAMA_MODEL="qwen2.5:3b"
$env:OLLAMA_TIMEOUT_SECONDS="30"
```

## Start API

```bash
uvicorn api.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Test chat

```bash
curl -X POST http://127.0.0.1:8000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain this product in one paragraph","mode":"open","remember":true}'
```

Expected response:

- `provider: ollama` if Ollama is running
- `provider: fallback` if Ollama is not available

## Memory API

```bash
curl -X POST http://127.0.0.1:8000/memory \
  -H "Content-Type: application/json" \
  -d '{"memory":"I prefer short direct answers."}'

curl http://127.0.0.1:8000/memory

curl -X DELETE http://127.0.0.1:8000/memory
```
