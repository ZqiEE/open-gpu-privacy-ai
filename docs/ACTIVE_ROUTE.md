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

## Route publication

`ra2.apply2()` publishes the active route only when:

```text
proof/trust gate passes
runtime doctor passes
model warm succeeds
```
