# Distillation strategy

Ailovanta should use distillation, but only with allowed teacher data.

## Goal

Use high-quality code answers to make the student model learn faster:

```text
teacher prompt/answer samples
-> normalized lesson corpus
-> mixed with GitHub code corpus
-> shard training
-> eval gate
-> promoted checkpoint
```

## Allowed teacher sources

Use:

```text
manual expert-written answers
user-owned outputs
company-owned outputs with permission
open model outputs when license allows it
synthetic examples created inside the project
approved benchmark explanations where allowed
```

Do not use:

```text
private third-party conversations without permission
bulk extraction from closed services
answers whose terms forbid training reuse
samples containing secrets, personal data, or credentials
```

## Teacher JSONL format

Each line:

```json
{"task":"code_generation","language":"python","source":"manual_teacher","score":1.0,"prompt":"Write a FastAPI health endpoint.","teacher":"from fastapi import FastAPI\n..."}
```

Supported answer fields:

```text
teacher
answer
completion
output
```

Supported prompt fields:

```text
prompt
instruction
question
```

## Build lesson corpus

```bash
copy runtime_data.example/teacher_code_samples.jsonl runtime_data/teacher_code_samples.jsonl

python scripts/distill_corpus.py \
  --input runtime_data/teacher_code_samples.jsonl \
  --output runtime_data/distill_corpus.jsonl \
  --min-score 0.8
```

## Mix with GitHub code corpus

```bash
python scripts/mix_corpus.py \
  --code runtime_data/code_corpus_github.jsonl \
  --lessons runtime_data/distill_corpus.jsonl \
  --output runtime_data/mixed_code_train.jsonl
```

## Train on mixed corpus

```bash
python scripts/full_local_loop.py \
  --api-url http://127.0.0.1:8000 \
  --data-file runtime_data/mixed_code_train.jsonl \
  --total-tokens 8192 \
  --shard-tokens 512 \
  --node-runs 8 \
  --model-id ailovanta-code-distill \
  --version v0.1-distill
```

## Release path

```text
train
-> scripts/check_code.py
-> scripts/ckpt_manifest.py
-> scripts/pool_store.py put
-> scripts/replica_book.py
-> scripts/promote_model.py --min-score 1.0
```

## Why this matters

Plain GitHub next-token training teaches syntax and patterns. Distillation teaches task behavior:

```text
how to answer coding requests
how to explain code
how to fix bugs
how to produce complete files
how to follow instruction format
```

The best path is not only raw code; it is raw code plus high-quality code instruction examples.
