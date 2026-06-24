# Ailovanta Owned Model Runtime

## Final target

Ailovanta should serve users through its own model loop:

```text
authorized data source
-> training job
-> ailovanta-core training round
-> validation and aggregation
-> promoted model artifact
-> runtime model manifest
-> trusted runtime node
-> chat/run response
-> feedback into future training jobs
```

## Runtime rule

When `AILOVANTA_REQUIRE_OWNED_MODEL=true`, Ailovanta must not silently fall back to a third-party bootstrap model.

If no verified Ailovanta runtime manifest is available, the API should say the owned model runtime is not ready instead of pretending it answered with the final model.

## Policy mode

The public product may support:

```text
standard
open_research
```

`open_research` means fewer product-level tone restrictions and broader research/creative answering. It does not mean support for harmful, illegal, privacy-invasive, or destructive requests.

## Current implementation boundary

`api/owned_model_runtime.py` adds the runtime contract:

```text
request
-> runtime router
-> verified Ailovanta runtime manifest required
-> owned runtime result placeholder
```

The next engineering step is to attach a real worker inference transport behind the verified runtime assignment.

## Next steps

1. Add `AILOVANTA_REQUIRE_OWNED_MODEL=true` mode to `/ailovanta/v1/chat`.
2. Register promoted artifacts from `ailovanta-core` as runtime manifests.
3. Add worker inference transport.
4. Route chat to verified runtime nodes.
5. Feed user-rated outputs back into future training jobs.
