# Deployment

This repository is still a local MVP. Use local deployment first.

## Local API

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```

## Docker

```bash
docker build -t open-gpu-privacy-ai .
docker run --rm -p 8000:8000 -v "$PWD/runtime_data:/app/runtime_data" open-gpu-privacy-ai
```

## Docker Compose

```bash
docker compose up --build
```

## Node client

```bash
python node_client/client.py --api-url http://127.0.0.1:8000 --contribution 30
```

## Production gaps

Before a public deployment, add:

- Authentication
- TLS
- Rate limits
- Signed jobs
- Sandboxed workers
- Database migration strategy
- Observability
- Abuse prevention
