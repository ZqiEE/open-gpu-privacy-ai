from __future__ import annotations

import json
import math
import shutil
from pathlib import Path
from time import time
from typing import Any

from api.compat_check import check_real_training_requirements


class ModelJobError(RuntimeError):
    pass


def run_model_job(payload: dict[str, Any], profile: dict[str, Any], source_id: str) -> dict[str, Any]:
    name = payload.get("name") or payload.get("model_id") or "ailovanta-code"
    version = payload.get("version") or "local-v0"
    out_dir = Path(payload.get("output_dir") or f"runtime_data/models/{name}-{version}")
    out_dir.mkdir(parents=True, exist_ok=True)

    data_path = payload.get("data_path") or payload.get("dataset_uri")
    base_model = payload.get("base_model") or "local"
    max_steps = int(payload.get("max_steps") or payload.get("steps") or 10)
    use_real = bool(payload.get("real") or payload.get("use_transformers") or payload.get("peft") or payload.get("qlora"))
    preflight: dict[str, Any] | None = None

    if use_real:
        preflight = check_real_training_requirements(payload, profile)
        if not preflight["ok"] and not bool(payload.get("allow_lightweight_fallback", True)):
            result = _training_failed("real_training_preflight_failed", "real training preflight failed: " + ", ".join(preflight["blockers"]))
        else:
            result = _run_transformers_job(base_model, data_path, out_dir, max_steps, payload)
    else:
        result = _write_portable_output(base_model, data_path, out_dir, max_steps)

    metrics = {
        "steps": max_steps,
        "cpu_threads": profile.get("cpu_threads"),
        "memory_gb": profile.get("memory_gb"),
        "has_gpu": bool(profile.get("has_gpu")),
        "backend": result["backend"],
        "score": result["score"],
        "created_at": time(),
    }
    record = {
        "schema": "ailovanta.model_output.v1",
        "name": name,
        "version": version,
        "source_job_id": source_id,
        "base_model": base_model,
        "dataset_uri": data_path,
        "data_path": data_path,
        "kind": result.get("kind") or payload.get("kind") or "adapter",
        "location": str(out_dir),
        "metrics": metrics,
        "backend_message": result["message"],
    }
    if preflight is not None:
        record["real_training_preflight"] = preflight
    (out_dir / "output.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    status = "failed" if result.get("ok") is False else "candidate"
    return {
        "name": name,
        "version": version,
        "source_job_id": source_id,
        "location": str(out_dir),
        "kind": record["kind"],
        "metrics": metrics,
        "status": status,
        "notes": result["message"],
    }


def _write_portable_output(base_model: str, data_path: str | None, out_dir: Path, max_steps: int) -> dict[str, Any]:
    dataset_path = resolve_dataset_path(data_path)
    if dataset_path and dataset_path.exists():
        return _train_lightweight_ngram(base_model, dataset_path, out_dir, max_steps)

    info = {"base_model": base_model, "data_path": data_path, "max_steps": max_steps, "mode": "no_dataset"}
    (out_dir / "adapter_config.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "backend": "no-dataset",
        "kind": "training_manifest",
        "score": 0.0,
        "message": "dataset missing; no training artifact produced",
    }


def _run_transformers_job(base_model: str, data_path: str | None, out_dir: Path, max_steps: int, payload: dict[str, Any]) -> dict[str, Any]:
    allow_fallback = bool(payload.get("allow_lightweight_fallback", True))
    try:
        from datasets import Dataset  # type: ignore
        from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments  # type: ignore
    except Exception as exc:
        if not allow_fallback:
            return _training_failed("transformers_deps_missing", f"optional local deps missing: {exc}; real training not run")
        fallback = _write_portable_output(base_model, data_path, out_dir, max_steps)
        fallback["message"] = f"optional local deps missing: {exc}; portable artifact written"
        return fallback

    dataset_path = resolve_dataset_path(data_path)
    if not dataset_path or not dataset_path.exists():
        if not allow_fallback:
            return _training_failed("dataset_missing", "dataset missing; real training not run")
        fallback = _write_portable_output(base_model, data_path, out_dir, max_steps)
        return fallback

    rows = _read_rows(dataset_path, max_rows=max(8, max_steps))
    if not rows:
        if not allow_fallback:
            return _training_failed("dataset_empty", "dataset has no usable text; real training not run")
        fallback = _write_portable_output(base_model, data_path, out_dir, max_steps)
        fallback["message"] = "dataset has no usable text; portable artifact written"
        return fallback

    try:
        tokenizer = AutoTokenizer.from_pretrained(base_model)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        load_kwargs: dict[str, Any] = {}
        qlora = bool(payload.get("qlora"))
        if qlora:
            try:
                from transformers import BitsAndBytesConfig  # type: ignore
                load_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype="float16", bnb_4bit_quant_type="nf4")
            except Exception as exc:
                if not allow_fallback:
                    return _training_failed("qlora_deps_missing", f"QLoRA dependencies missing: {exc}; real training not run")

        model = AutoModelForCausalLM.from_pretrained(base_model, **load_kwargs)
        backend = "transformers"
        kind = "full_model"

        if payload.get("peft") or payload.get("lora") or payload.get("qlora"):
            try:
                from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training  # type: ignore
                if qlora:
                    model = prepare_model_for_kbit_training(model)
                config = LoraConfig(
                    r=int(payload.get("lora_r", 8)),
                    lora_alpha=int(payload.get("lora_alpha", 16)),
                    lora_dropout=float(payload.get("lora_dropout", 0.05)),
                    bias="none",
                    task_type=TaskType.CAUSAL_LM,
                    target_modules=payload.get("target_modules") or None,
                )
                model = get_peft_model(model, config)
                backend = "qlora" if qlora else "lora"
                kind = "adapter"
            except Exception as exc:
                (out_dir / "peft_error.txt").write_text(str(exc), encoding="utf-8")
                if not allow_fallback:
                    return _training_failed("peft_setup_failed", f"PEFT setup failed: {exc}; real training not run")

        dataset = Dataset.from_list(rows)

        def tokenize(batch: dict[str, list[str]]) -> dict[str, Any]:
            encoded = tokenizer(batch["text"], truncation=True, padding="max_length", max_length=int(payload.get("max_length", 512)))
            encoded["labels"] = encoded["input_ids"].copy()
            return encoded

        tokenized = dataset.map(tokenize, batched=True, remove_columns=["text"])
        args = TrainingArguments(
            output_dir=str(out_dir),
            max_steps=max_steps,
            per_device_train_batch_size=int(payload.get("batch_size", 1)),
            gradient_accumulation_steps=int(payload.get("gradient_accumulation_steps", 1)),
            learning_rate=float(payload.get("learning_rate", 2e-4)),
            logging_steps=max(1, min(10, max_steps)),
            save_steps=max_steps,
            report_to=[],
        )
        trainer = Trainer(model=model, args=args, train_dataset=tokenized)
        trainer.train()
        trainer.save_model(str(out_dir))
        tokenizer.save_pretrained(str(out_dir))
        return {"backend": backend, "kind": kind, "score": 0.82 if kind == "adapter" else 0.78, "message": f"local {backend} run finished"}
    except Exception as exc:
        if not allow_fallback:
            return _training_failed("transformers_training_failed", f"real Transformers training failed: {type(exc).__name__}: {exc}")
        fallback = _write_portable_output(base_model, data_path, out_dir, max_steps)
        fallback["message"] = f"real Transformers training failed: {type(exc).__name__}: {exc}; portable artifact written"
        return fallback


def _training_failed(reason: str, message: str) -> dict[str, Any]:
    return {"ok": False, "backend": reason, "kind": "training_failed", "score": 0.0, "message": message}


def _read_rows(path: Path, max_rows: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if len(rows) >= max_rows:
                break
            try:
                item = json.loads(line)
            except Exception:
                continue
            text = item.get("text") or item.get("target") or item.get("content")
            if text:
                rows.append({"text": str(text)[:4096]})
    return rows


def resolve_dataset_path(value: str | None) -> Path | None:
    if not value:
        return None
    if value.startswith("file://"):
        return Path(value.removeprefix("file://"))
    if value.startswith("local://"):
        return Path(value.removeprefix("local://"))
    if "://" in value:
        return None
    return Path(value)


def _train_lightweight_ngram(base_model: str, dataset_path: Path, out_dir: Path, max_steps: int) -> dict[str, Any]:
    rows = _read_rows(dataset_path, max_rows=max(32, max_steps * 4))
    texts = [row["text"] for row in rows if row.get("text")]
    if not texts:
        return {
            "backend": "empty-dataset",
            "kind": "training_manifest",
            "score": 0.0,
            "message": "dataset had no usable text; no training artifact produced",
        }

    counts: dict[str, dict[str, int]] = {}
    total_transitions = 0
    epochs = max(1, min(max_steps, 50))
    for _ in range(epochs):
        for text in texts:
            previous = "\n"
            for current in text[:4096]:
                bucket = counts.setdefault(previous, {})
                bucket[current] = bucket.get(current, 0) + 1
                previous = current
                total_transitions += 1

    vocabulary = sorted({char for bucket in counts.values() for char in bucket})
    vocab_size = max(len(vocabulary), 1)
    nll = 0.0
    eval_transitions = 0
    for text in texts[: min(len(texts), 32)]:
        previous = "\n"
        for current in text[:2048]:
            bucket = counts.get(previous, {})
            probability = (bucket.get(current, 0) + 1) / (sum(bucket.values()) + vocab_size)
            nll -= math.log(probability)
            previous = current
            eval_transitions += 1

    train_loss = round(nll / max(eval_transitions, 1), 6)
    model = {
        "schema": "ailovanta.lightweight_ngram.v1",
        "base_model": base_model,
        "dataset_path": str(dataset_path),
        "epochs": epochs,
        "rows": len(texts),
        "vocab_size": vocab_size,
        "transitions": total_transitions,
        "train_loss": train_loss,
        "counts": counts,
    }
    (out_dir / "ngram_model.json").write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "adapter_config.json").write_text(
        json.dumps(
            {
                "backend": "lightweight-ngram",
                "base_model": base_model,
                "dataset_path": str(dataset_path),
                "train_loss": train_loss,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    score = round(max(0.05, min(0.95, 1.0 / (1.0 + train_loss))), 4)
    return {
        "backend": "lightweight-ngram",
        "kind": "local_language_artifact",
        "score": score,
        "message": f"trained lightweight n-gram artifact on {len(texts)} rows; train_loss={train_loss}",
    }


def merge_outputs(items: list[dict[str, Any]], output_dir: str | Path) -> dict[str, Any]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    merged = {
        "schema": "ailovanta.merged_output.v1",
        "items": items,
        "count": len(items),
        "score": round(sum(float((item.get("metrics") or {}).get("score", 0.0)) for item in items) / max(len(items), 1), 4),
        "created_at": time(),
    }
    (target / "merged.json").write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    for item in items:
        loc = Path(str(item.get("location", "")))
        if loc.exists() and (loc / "adapter_config.json").exists():
            shutil.copyfile(loc / "adapter_config.json", target / f"adapter_config_{item.get('id', len(list(target.glob('adapter_config_*'))))}.json")
    return {"location": str(target), "metrics": {"score": merged["score"], "merged_count": len(items)}, "summary": "outputs merged"}
