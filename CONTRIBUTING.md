# Contributing to Ailovanta

Ailovanta is a public shell and local MVP for a distributed AI compute network.

## Before contributing

Please read:

- `README.md`
- `BRAND.md`
- `SECURITY_BOUNDARY.md`
- `docs/PROJECT_STATUS.md`
- `docs/LOCAL_RUNTIME.md`

## Local checks

Run these before opening a pull request:

```bash
python validate.py
python -m pytest -q
```

## Good contributions

Good public-repository contributions include:

- public docs
- local API examples
- node client improvements
- tests
- dashboard polish
- public SDK stubs
- safer worker shell improvements
- local developer tooling

## Keep out of the public repository

Do not add:

- credentials
- private environment files
- model weights
- private datasets
- generated runtime databases
- logs containing user data
- core network coordination logic that belongs in Ailovanta Core

## Project discipline

Do not claim that Ailovanta has already solved global distributed training. The current public repository is a local MVP and public interface layer.
