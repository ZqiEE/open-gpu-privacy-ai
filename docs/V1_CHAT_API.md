# V1 Chat API

Ailovanta provides a local chat endpoint that follows the common chat-completions shape used by many AI clients.

## Endpoint

```text
POST /v1/chat/completions
```

## Start the API

```bash
uvicorn api.main:app --reload
```

## Call it

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ailovanta-local",
    "messages": [
      {"role": "user", "content": "Explain Ailovanta in one sentence."}
    ]
  }'
```

## Runtime behavior

If a local Ollama runtime is available, Ailovanta calls it.

If Ollama is not available, the endpoint returns a safe local fallback response instead of crashing. This keeps clients working during local setup.

## Current limitation

Streaming is not supported in this local MVP yet.
