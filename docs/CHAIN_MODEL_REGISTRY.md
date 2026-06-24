# Chain Model Registry

## Correction

`ailovanta-owned:candidate` should not be treated as only a local model tag.

It should be a model identity that can be verified through:

```text
model_id
version
artifact_hash
runtime_manifest_hash
chain event hash
optional blockchain transaction
```

## Purpose

Ailovanta uses Web3-style registry semantics for model ownership and runtime trust.

The model is not only a file name. It is an identity record:

```text
who trained it
which training job produced it
which artifact hash represents it
which runtime manifest serves it
which node claims to cache it
which chain event anchors the claim
```

## Current implementation

`api/chain_registry.py` provides a local append-only ledger:

```text
previous_event_hash
-> event payload
-> event_hash
```

This creates chain-style continuity before deploying to a public blockchain or smart contract.

## Event types

```text
model_artifact_promoted
runtime_manifest_registered
worker_attested
```

## Target chain flow

```text
ailovanta-core artifact
-> artifact_hash
-> public runtime manifest
-> chain event
-> optional smart contract anchor
-> worker attestation
-> owned-chat runtime route
```

## Why this matters

When users call `ailovanta-owned:candidate`, the system should verify that the model identity is backed by an artifact hash and a registry event, not just trust a local string.

## Future blockchain adapter

The local chain registry can be mirrored to:

```text
EVM contract
Solana program
Arweave/IPFS metadata anchor
custom appchain
```

The production requirement is simple:

```text
No chain/artifact record, no final owned-model claim.
```
