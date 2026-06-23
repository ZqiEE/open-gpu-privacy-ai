# Ailovanta Repository Settings

These are the recommended GitHub repository settings for the public repository.

## Repository name

```text
ailovanta
```

## Description

```text
Ailovanta is a distributed AI compute network MVP with a local API, node client, dashboard, verification, training job records, and public/core architecture boundary.
```

## Website

Use the production website when available:

```text
https://ailovanta.com
```

For now, leave empty if the domain is not connected yet.

## Topics

Recommended topics:

```text
ai
artificial-intelligence
distributed-compute
compute-network
fastapi
node-client
scheduler
training
inference
local-ai
ollama
```

## Social preview

Use a dark branded image with:

```text
Ailovanta
AI powered by the world's distributed compute.
```

## Branch protection

Recommended before external collaborators:

- Require pull request before merging.
- Require status checks to pass.
- Require `Ailovanta CI`.
- Disallow force pushes to `main`.
- Disallow deletion of `main`.

## Actions

If GitHub asks to enable workflows, enable Actions for this repository.

Expected workflow:

```text
.github/workflows/validate.yml
```

Expected checks:

```bash
python validate.py
python -m pytest -q
```
