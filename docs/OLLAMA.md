# Ollama Local Bootstrap Runtime

The API can call a local Ollama runtime during development. This is a bootstrap path for the public MVP, not the final Ailovanta-owned model backend.

## Boundary

```text
Current: Ailovanta API -> local Ollama bootstrap model
Target:  Ailovanta API -> runtime router -> verified Ailovanta runtime manifest
```

This path is not Alibaba Cloud and does not use DashScope. If you configure a third-party open model in Ollama, it is only a temporary local bootstrap model.

## Install Ollama

Install Ollama from the official app for your OS, then start it.

## Pull a local bootstrap model

Recommended small model for local testing:

```bash
ollama pull llama3.2:3b
```

You can also use another local model you have already pulled:

```bash
ollama pull mistral:7b
```

## Configure model

Create a `.env` or export environment variables before starting the API:

```bash
export AILOVANTA_MODEL_STAGE=bootstrap_local_runtime
export AILOVANTA_OWNED_MODEL_READY=false
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export OLLAMA_MODEL=llama3.2:3b
export OLLAMA_TIMEOUT_SECONDS=30
```

Windows PowerShell:

```powershell
$env:AILOVANTA_MODEL_STAGE="bootstrap_local_runtime"
$env:AILOVANTA_OWNED_MODEL_READY="false"
$env:OLLAMA_BASE_URL="http://127.0.0.1:11434"
$env:OLLAMA_MODEL="llama3.2:3b"
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
curl -X POST http://127.0.0.1:8000/ailovanta/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain this product in one paragraph","user_id":"local"}'
```

Expected response:

- `source: ollama` if Ollama is running
- `source: fallback` if Ollama is not available

## Health check

```bash
curl http://127.0.0.1:8000/health
```

The `local_model` field states whether the API is still using the bootstrap local runtime or a future Ailovanta-owned model backend.
