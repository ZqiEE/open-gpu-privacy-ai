from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.artifact_binding import ArtifactBindingStore
from api.runtime_ref import to_local_path


class BoundRuntimeUnavailable(RuntimeError):
    pass


class ArtifactBoundRuntime:
    def __init__(self, binding_store: ArtifactBindingStore | None = None) -> None:
        self.binding_store = binding_store or ArtifactBindingStore()

    def chat(self, prompt: str, model_id: str, version: str) -> dict[str, Any]:
        model_key = f"{model_id}:{version}"
        binding = self.binding_store.latest_for_model_statuses(model_key, ("active",))
        if not binding:
            raise BoundRuntimeUnavailable("no active artifact binding for " + model_key)
        backend_kind = binding.get("backend_kind") or "checkpoint-artifact"
        backend_ref = binding.get("backend_ref") or binding.get("checkpoint_uri") or ""
        if backend_kind in {"transformers-local", "transformers-causal-lm"}:
            answer = self._chat_transformers(prompt, backend_ref)
            return {"answer": answer, "source": "artifact-bound-transformers", "binding": binding}
        if backend_kind == "lightweight-ngram":
            answer = self._chat_lightweight_ngram(prompt, backend_ref, binding)
            return {"answer": answer, "source": "artifact-bound-lightweight-ngram", "binding": binding}
        if backend_kind in {"jsonl-stat", "checkpoint-artifact"}:
            answer = self._chat_checkpoint_summary(prompt, backend_ref, binding)
            return {"answer": answer, "source": "artifact-bound-checkpoint", "binding": binding}
        raise BoundRuntimeUnavailable("unsupported artifact binding backend: " + backend_kind)

    def _chat_checkpoint_summary(self, prompt: str, backend_ref: str, binding: dict[str, Any]) -> str:
        path = resolve_local_ref(backend_ref)
        checkpoint = read_json_file(path)
        if checkpoint:
            return build_checkpoint_bound_answer(prompt, binding, checkpoint)
        raise BoundRuntimeUnavailable("binding has no loadable local checkpoint: " + str(backend_ref))

    def _chat_lightweight_ngram(self, prompt: str, backend_ref: str, binding: dict[str, Any]) -> str:
        path = resolve_local_ref(backend_ref)
        model = read_json_file(path)
        if not model:
            raise BoundRuntimeUnavailable("binding has no loadable lightweight ngram model: " + str(backend_ref))
        return build_lightweight_ngram_answer(prompt, binding, model)

    def _chat_transformers(self, prompt: str, backend_ref: str) -> str:
        path = resolve_local_ref(backend_ref)
        if not path or not path.exists():
            raise BoundRuntimeUnavailable("transformers model path not found: " + str(backend_ref))
        try:
            import torch  # type: ignore
            from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
        except Exception as exc:
            raise BoundRuntimeUnavailable("transformers runtime requires torch and transformers") from exc
        tokenizer = AutoTokenizer.from_pretrained(str(path))
        model = AutoModelForCausalLM.from_pretrained(str(path))
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)
        model.eval()
        encoded = tokenizer(prompt, return_tensors="pt").to(device)
        output = model.generate(**encoded, max_new_tokens=128, do_sample=False)
        text = tokenizer.decode(output[0], skip_special_tokens=True)
        return text[len(prompt) :].strip() or text.strip()


def resolve_local_ref(value: str) -> Path | None:
    return to_local_path(value)


def read_json_file(path: Path | None) -> dict[str, Any] | None:
    if not path or not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"checkpoint_path": str(path)}


def build_checkpoint_bound_answer(prompt: str, binding: dict[str, Any], checkpoint: dict[str, Any]) -> str:
    text = prompt.strip()
    lowered = text.lower()
    model_key = binding.get("model_key") or "ailovanta-owned:candidate"
    artifact_hash = binding.get("artifact_hash") or "local-artifact"
    backend = checkpoint.get("backend") or binding.get("backend_kind") or "checkpoint-artifact"

    if asks_training_status(text, lowered):
        return cn(
            "没有。当前 runtime 只加载了 bootstrap/checkpoint 元数据，不是自训练完成的大模型权重。"
            "训练流程可以运行，但这个绑定本身不能证明模型已经训练好，也不能冒充会对话或会写代码的模型。"
        )
    if asks_model_identity(text, lowered):
        return cn(
            f"当前不是已训练完成的大模型。model={model_key}，artifact={artifact_hash}，backend={backend}。"
            "这是 runtime/checkpoint 绑定状态，不是可生成代码的自训练权重。"
        )
    if asks_code_ability(text, lowered):
        return cn("当前这个绑定不会写代码。它不是通过训练得到的代码生成模型；必须接入并通过评测的 Transformers/LoRA 权重后才算。")
    if asks_persona(text, lowered):
        return cn("我没有真实性别。当前回答来自 Ailovanta runtime 状态层，不是自训练大模型人格。")
    if is_greeting(text, lowered):
        return cn("我在。Ailovanta runtime 已接通，但当前不是已训练完成的自有大模型。")
    return cn("当前只能报告 runtime/checkpoint 绑定状态；没有已激活的自训练生成模型在回答这个问题。")


def build_lightweight_ngram_answer(prompt: str, binding: dict[str, Any], model: dict[str, Any]) -> str:
    text = prompt.strip()
    lowered = text.lower()
    rows = int(model.get("rows") or 0)
    loss = model.get("train_loss")
    transitions = int(model.get("transitions") or 0)
    artifact_hash = binding.get("artifact_hash") or "local-artifact"

    if asks_code_ability(text, lowered):
        return cn(
            "不会。当前绑定的是 lightweight-ngram 训练链路证明，不是能写代码的自训练大模型。"
            f"artifact={artifact_hash}，rows={rows}，transitions={transitions}，train_loss={loss}。"
            "只有 Transformers/LoRA 权重通过可执行代码生成 benchmark 后，才能说模型会写代码。"
        )
    if asks_persona(text, lowered):
        return cn("我没有真实性别。当前不是自训练大模型人格，只是 runtime 对 lightweight-ngram 状态的说明。")
    if asks_training_status(text, lowered):
        return cn(
            "严格说：没有训练出可对话/可写代码的大模型。"
            f"现在只有 lightweight-ngram 训练链路证明，rows={rows}，transitions={transitions}，train_loss={loss}。"
            "它说明 worker 跑过训练步骤，但不等于自训练大模型已经可用。"
        )
    if asks_model_identity(text, lowered):
        return cn(
            f"当前不是大模型。runtime 绑定的是 lightweight-ngram artifact={artifact_hash}，rows={rows}，train_loss={loss}。"
            "这是训练流程的轻量证明，不是可生成代码的自训练权重。"
        )
    if is_greeting(text, lowered):
        return cn("我在。当前 runtime 有 lightweight-ngram 绑定，但还没有已训练完成的自有大模型在回答。")
    return cn(f"当前只有 lightweight-ngram 训练链路证明，rows={rows}，train_loss={loss}；还不是自训练生成模型。")


def asks_training_status(text: str, lowered: str) -> bool:
    return any(phrase in lowered for phrase in ("trained", "self trained", "self-trained", "training")) or contains_any(
        text,
        (
            "训练",
            "自训",
            "自己训",
            "自己训练",
            "你训练了",
            "是自己训练的吗",
            "是不是自己训练",
        ),
    )


def asks_model_identity(text: str, lowered: str) -> bool:
    return any(phrase in lowered for phrase in ("what model", "which model", "model are you", "llm")) or contains_any(
        text,
        ("什么大模型", "哪个大模型", "你是什么模型", "你是什么大模型", "模型是什么"),
    )


def asks_code_ability(text: str, lowered: str) -> bool:
    return any(phrase in lowered for phrase in ("write code", "coding", "program")) or contains_any(
        text,
        ("写代码", "会代码", "编程", "代码吗", "敲代码"),
    )


def asks_persona(text: str, lowered: str) -> bool:
    return any(phrase in lowered for phrase in ("female", "girl", "woman", "male", "boy", "gender")) or contains_any(
        text,
        ("女的吗", "男的吗", "性别", "女生", "女孩", "男生"),
    )


def is_greeting(text: str, lowered: str) -> bool:
    return any(word in lowered for word in ("hello", "hi", "hey")) or contains_any(text, ("你好", "在吗", "在不在"))


def contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def cn(value: str) -> str:
    return value
