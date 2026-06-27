# Active Route

Ailovanta stores the current owned-chat default model in `RouteBook`.

Default route key:

```text
owned-chat/default
```

## Read current route

```bash
python scripts/route_book.py get --route-key owned-chat/default
```

## Set route manually

```bash
python scripts/route_book.py set \
  --route-key owned-chat/default \
  --model-key ailovanta-owned:candidate
```

## Disable route

```bash
python scripts/route_book.py disable \
  --route-key owned-chat/default \
  --reason rollback
```

## Route health

Check whether the active route is actually usable:

```bash
python scripts/route_health.py --route-key owned-chat/default
```

Disable it automatically if it is bad:

```bash
python scripts/route_health.py --route-key owned-chat/default --disable-if-bad
```

API:

```text
GET  /route-health/owned-chat/default
POST /route-health/check
```

Health checks include:

```text
route exists and is active
artifact binding exists and is active/candidate
runtime doctor reports ready
```

With artifact verification enabled, health also checks:

```text
binding checkpoint_uri/backend_ref is fetchable
artifact bytes match artifact_hash
bad artifact can disable the active route
```

API:

```text
GET /route-health/owned-chat/default?verify_artifact=true
POST /route-health/check {"route_key":"owned-chat/default","disable_if_bad":true,"verify_artifact":true}
```

## Chat through active route

```text
POST /ailovanta/v1/owned-chat-default
```

Payload:

```json
{
  "prompt": "hello",
  "user_id": "local"
}
```

This endpoint does not require model_id/version. It loads them from the active route.

If no active route exists, it returns `owned-route-unavailable`.

If the route exists but fails health checks, it returns `owned-route-unhealthy`.

## Route publication

`ra2.apply2()` publishes the active route only when:

```text
proof/trust gate passes
artifact integrity gate passes when enabled
runtime doctor passes
model warm succeeds
```

Enable artifact verification for route publication:

```bash
export AILOVANTA_VERIFY_ROUTE_ARTIFACT=true
```

Or pass `verify_artifact=true` to the apply API:

```json
{
  "result_path": "runtime_data/local_loop/foundation_result.json",
  "runtime_id": "rt-owned-1",
  "node_id": "node-owned-1",
  "verify_artifact": true
}
```

If the artifact cannot be fetched or its sha256 does not match, apply will not warm or publish the route.

## Rollback behavior

`RollbackExecutor` now checks active routes during rollback.

If an active route points to the bad model, rollback will disable that route:

```text
owned-chat/default -> bad:model
rollback bad:model
=> owned-chat/default disabled
```

If the live record contains a `previous_model`, rollback restores the same route to the previous model:

```text
owned-chat/default -> bad:model
previous_model = stable:model
rollback bad:model
=> owned-chat/default -> stable:model
```

This prevents `/ailovanta/v1/owned-chat-default` from continuing to route traffic to a rolled-back model.
