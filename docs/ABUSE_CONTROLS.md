# Abuse Controls

Use the abuse-ready app entry for public deployments:

```bash
uvicorn api.main_abuse_ready:app --host 0.0.0.0 --port 8000
```

Required production settings:

```text
AILOVANTA_RATE_LIMIT_ENABLED=true
AILOVANTA_RATE_LIMIT_PER_MINUTE=120
AILOVANTA_RATE_LIMIT_WINDOW_SECONDS=60
AILOVANTA_ADMIN_TOKEN=<secret>
```

Check enhanced readiness:

```text
GET /ops/readiness/plus?route_key=owned-chat/default&verify_bytes=true
```

This includes:

```text
route health
artifact byte checks
verified runtime routing
rate limit status
admin token status
```

If rate limiting is off, enhanced readiness returns a blocker.
