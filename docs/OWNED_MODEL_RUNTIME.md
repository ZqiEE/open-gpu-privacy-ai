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
-> worker /v1/owned/infer
-> artifact-bound result
-> worker result validation receipt
```

Owned chat can run with `AILOVANTA_REQUIRE_OWNED_MODEL=true`. In this mode it does not silently fall back to bootstrap/Ollama text.

The chat response includes:

```text
worker_validation.receipt_id
worker_validation.passed
worker_validation.blockers
worker_validation.sampled_chunks
```

The receipt ties the answer to the selected runtime manifest, artifact binding, optional artifact chunk manifest sample, and reputation event.

## Next steps

1. Add `AILOVANTA_REQUIRE_OWNED_MODEL=true` mode to `/ailovanta/v1/chat`. Done locally.
2. Register promoted artifacts from `ailovanta-core` as runtime manifests.
3. Add worker inference transport. Done locally through runtime endpoint registry or worker URL env.
4. Route chat to verified runtime nodes. Done locally for owned-required chat mode.
5. Feed user-rated outputs back into future training jobs.
