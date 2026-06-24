# Asset Index

## Purpose

Ailovanta needs a public-side index for promoted model assets.

The runtime layer already routes by model key and manifest hash. The asset index adds a place to store the full asset payload for that hash.

## Flow

```text
core asset payload
-> public asset index
-> runtime manifest hash
-> trusted node cache key
-> worker loads matching asset
```

## API module

```text
api.asset_api
```

It exposes:

```text
POST /model-assets
GET /model-assets
GET /model-assets/{digest}
```

## Storage

Records are written as JSON files under:

```text
runtime_data/assets
```

## Next step

Wire `api.asset_api.router` into the owned app entrypoint and make worker startup verify that the requested manifest hash exists in the asset index before serving.
