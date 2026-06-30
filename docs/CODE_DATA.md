# Code-first data strategy

Ailovanta should not start with random whole-web scraping. The useful path is:

```text
trusted / allowed code sources
-> GitHub broad discovery
-> instruction-first corpus builder
-> raw code foundation corpus builder
-> shard jobs
-> verified deltas
-> merged code checkpoint
-> code-first runtime
```

## Why code first

Code ability is easier to evaluate than general chat:

```text
unit tests
syntax checks
type checks
lint checks
benchmark prompts
repository repair tasks
```

That means Ailovanta can improve through measurable feedback instead of only subjective chat scoring.

See `docs/AILOVANTA_CODE_TRAINING_SYSTEM.md` for the full three-layer algorithm:

```text
language foundation -> engineering structure -> task execution
```

## Source policy

Preferred sources:

```text
user-owned repositories
company-owned repositories with permission
public repositories with clear permissive licenses
public domain / permissive examples
docs and code snippets explicitly allowed for training/use
```

Avoid by default:

```text
private code without permission
unclear-license code
sites that disallow automated access
credentials, secrets, API keys, tokens
personal data inside repositories
large vendored dependency folders
node_modules / .venv / build artifacts
```

## Local code corpus

Build a code corpus from a local folder:

```bash
python scripts/code_corpus.py \
  --source . \
  --output runtime_data/code_corpus.jsonl
```

Train code-first local loop:

```bash
python scripts/train_code_loop.py \
  --api-url http://127.0.0.1:8000 \
  --source . \
  --total-tokens 4096 \
  --shard-tokens 512 \
  --node-runs 8
```

Outputs:

```text
runtime_data/code_corpus.jsonl
runtime_data/model_deltas/<plan_id>/*.pt
runtime_data/didx.json
runtime_data/credits.json
runtime_data/merged_models/*.pt
```

## Future web ingestion

Automatic web ingestion should be a policy-controlled crawler, not blind scraping:

```text
seed URLs / allowed domains
robots and rate limits
content hash deduplication
license / terms metadata
secret scanning
PII filtering
poison filtering
source manifest
opt-out / removal list
```

The first production crawler should only add sources that pass the manifest policy. The crawler should write source metadata beside every training record.

## Authorized broad GitHub ingestion

For owner-controlled or explicitly authorized code, Ailovanta can use a broad ingestion mode:

```text
license_policy = private_owner_unrestricted
license_policy = authorized_unrestricted
license_policy = shareholder_authorized
license_policy = explicit_permission
license_policy = internal
```

These policies allow ingestion even when public license metadata is unknown, because the source manifest itself is the authorization record. This is intended for code the operator owns, controls, or has explicit permission to use.

Public/shared model builds should still use `public_safe` or `public_permissive` when the source is not operator-authorized.

Run the full authorized ingest path:

```bash
python scripts/ingest_github_code.py \
  --sources runtime_data/github_code_sources.json \
  --corpus-output runtime_data/code_corpus_github.jsonl \
  --rights-path runtime_data/rights_proofs.json \
  --jobs-path runtime_data/code_training_jobs.json \
  --corpus-mode instructions \
  --create-job
```

The ingest path performs:

```text
fetch or use local repo
secret scan
large/vendor directory filtering
instruction-first JSONL write by default
raw code JSONL write when --corpus-mode code is used
rights proof registration
optional distributed code training job creation
```

Even in broad authorized mode, secrets, tokens, private keys, build outputs, vendored dependencies, and unreadable files are filtered out before training records are written.

For the local automatic path, use:

```powershell
.\start_auto_training_windows.bat -Server http://127.0.0.1:8001
.\start_training_worker_windows.bat -Server http://127.0.0.1:8001
```

The automatic path performs:

```text
GitHub source discovery
-> source manifest update
-> bounded fetch
-> instruction/code corpus generation
-> training JSONL generation
-> /training/jobs queue submission
-> worker training
-> artifact binding into owned runtime
```

Use `-Loop` on `start_auto_training_windows.bat` to keep discovering and queuing new jobs periodically.

For low-level syntax, spelling, AST shape, and API usage training, run:

```bash
python scripts/ingest_github_code.py \
  --sources runtime_data/github_code_sources.json \
  --corpus-mode code
```

For combined instruction and raw code records:

```bash
python scripts/ingest_github_code.py \
  --sources runtime_data/github_code_sources.json \
  --corpus-mode mixed \
  --create-job
```

## Evaluation first

For code training, every checkpoint should be evaluated by:

```text
Python syntax compile
TypeScript build / typecheck where available
unit tests where available
patch-based repair tasks
known coding benchmarks
security pattern checks
```

Only checkpoints that improve code evals should be promoted.
