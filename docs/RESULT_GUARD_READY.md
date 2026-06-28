# Result Guard Readiness

Commercial checklist item:

```text
worker result requires valid node proof
```

Probe API:

```text
GET /ops/result-guard/ready
```

The check verifies:

```text
missing node mark is rejected
wrong node mark is rejected
configured node mark is accepted
```

Production must configure node secrets, for example:

```text
AILOVANTA_NODE_SECRETS_JSON={"node-1":"replace-me"}
```

If no node secret map exists, `prod_ready_plus` returns:

```text
result_guard:node_secret_map_missing
```

Release gate calls `prod_ready_plus`, so a failed result guard blocks `release_pass`.
