from __future__ import annotations

from typing import Any


def run_qlora_smoke(base_model: str = "sshleifer/tiny-gpt2") -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False, "base_model": base_model, "checks": []}
    try:
        import torch  # type: ignore
        result["checks"].append({"name": "torch", "ok": True, "version": getattr(torch, "__version__", "unknown"), "cuda": bool(torch.cuda.is_available())})
    except Exception as exc:
        result["checks"].append({"name": "torch", "ok": False, "error": str(exc)})
        return result

    try:
        import bitsandbytes as bnb  # type: ignore
        result["checks"].append({"name": "bitsandbytes", "ok": True, "version": getattr(bnb, "__version__", "unknown")})
    except Exception as exc:
        result["checks"].append({"name": "bitsandbytes", "ok": False, "error": str(exc)})
        return result

    try:
        from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training  # type: ignore
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig  # type: ignore

        quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype="float16", bnb_4bit_quant_type="nf4")
        tokenizer = AutoTokenizer.from_pretrained(base_model)
        model = AutoModelForCausalLM.from_pretrained(base_model, quantization_config=quant)
        model = prepare_model_for_kbit_training(model)
        config = LoraConfig(r=4, lora_alpha=8, lora_dropout=0.05, bias="none", task_type=TaskType.CAUSAL_LM)
        model = get_peft_model(model, config)
        tokens = tokenizer("hello", return_tensors="pt")
        _ = model(**tokens)
        result["checks"].append({"name": "qlora_forward", "ok": True})
        result["ok"] = True
        return result
    except Exception as exc:
        result["checks"].append({"name": "qlora_forward", "ok": False, "error": str(exc)})
        return result
