# Ailovanta Security Boundary

This repository is the public interface and demonstration layer for Ailovanta.

## Public layer

The public layer may include:

- high-level README
- public roadmap
- SDK stubs
- demo scripts
- mock adapters
- public contract drafts
- contribution guidelines
- non-sensitive tests
- public node shell

## Private core layer

The following must stay outside this public repository:

- production model packages
- production datasets
- private routing logic
- production reward logic
- production validator logic
- production anti-abuse logic
- guardian operations
- runtime approval logic
- deployment credentials
- cloud configuration
- node operator private keys
- any secret material

## Asset layer

The asset layer must never be committed to Git:

- model weights
- adapters
- datasets
- generated runtime databases
- logs containing user data
- private environment files
- private object store snapshots

## Repositories

Public repository:

```text
https://github.com/ZqiEE/ailovanta.git
```

Private core repository:

```text
https://github.com/ZqiEE/ailovanta-core.git
```

## Rule

Public code should explain how the network works. Private code and assets should make the network defensible.
