# Deploy Review

This gate makes public deployment checks machine-readable.

It checks HTTPS public URL, non-local production storage, non-local production anchor, remote worker/model modes, node proof, rate limit, admin token, and secret redaction.

Use:

```text
GET /ops/readiness/plus?route_key=owned-chat/default&verify_bytes=true
GET /ops/alerts/summary?route_key=owned-chat/default&verify_bytes=true
```

Deploy review blockers use the `review:` prefix. Do not treat production as ready while these blockers exist.
