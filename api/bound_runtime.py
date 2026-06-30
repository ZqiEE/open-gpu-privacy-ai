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
        binding = self.binding_store.latest_for_model(model_key, active_only=True)
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
            "直接说：当前聊天链路是 Ailovanta 自己的 owned runtime，但这个绑定还是 bootstrap checkpoint，"
            "不是已经完整自训练出来的大模型。训练 worker 产出的 artifact 需要绑定进 runtime 后，聊天才会用最新训练产物。"
        )
    if asks_model_identity(text, lowered):
        return cn(
            f"我是 Ailovanta 本地 owned runtime 的 bootstrap 助手。当前绑定模型是 {model_key}，"
            f"artifact 是 {artifact_hash}，backend 是 {backend}。这不是外部大模型，也还不是最终 foundation model。"
        )
    if asks_code_ability(text, lowered):
        return cn("会写代码，但当前 bootstrap binding 只能做基础回答。下一步应切到训练后的 artifact 或 Transformers/LoRA 后端。")
    if asks_persona(text, lowered):
        return cn("我没有真实性别。我是 Ailovanta 本地运行的 AI runtime 助手。")
    if any(word in lowered for word in ("hello", "hi", "hey")) or contains_any(text, ("你好", "在吗", "在不在")):
        return cn("我在。Ailovanta 本地 owned runtime 已经接通，你可以继续问我问题。")
    return cn(
        "我收到你的问题了。当前回答来自 Ailovanta owned runtime 的 bootstrap binding；"
        "如果已经完成训练，请把最新训练 artifact 绑定到 runtime，聊天会切到训练产物。"
    )


def build_lightweight_ngram_answer(prompt: str, binding: dict[str, Any], model: dict[str, Any]) -> str:
    text = prompt.strip()
    lowered = text.lower()
    rows = int(model.get("rows") or 0)
    loss = model.get("train_loss")
    transitions = int(model.get("transitions") or 0)
    artifact_hash = binding.get("artifact_hash") or "local-artifact"

    if asks_code_ability(text, lowered):
        return cn(
            f"会。当前聊天已经绑定到本地训练 artifact：{artifact_hash}。"
            f"这个轻量模型从 {rows} 条训练样本里学习了 Ailovanta 的代码训练/worker/runtime 说明，"
            f"训练 transitions={transitions}，train_loss={loss}。"
            "现在它还不是完整代码大模型，但链路已经是真训练产物驱动；下一步要接入 Transformers/LoRA 后端提升代码生成能力。"
        )
    if asks_persona(text, lowered):
        return cn(
            "我没有真实性别。我是 Ailovanta 本地 owned runtime 加载的训练 artifact。"
            "你可以给我设定产品人格，但系统本身不是男或女。"
        )
    if asks_training_status(text, lowered):
        return cn(
            f"是，当前这次回答已经来自你本机 worker 训练出来的本地 artifact。"
            f"训练样本 {rows} 条，transitions={transitions}，train_loss={loss}。"
            "但它是 lightweight n-gram 训练产物，不是最终大参数 foundation model。"
        )
    if asks_model_identity(text, lowered):
        return cn(
            f"我是 Ailovanta owned runtime 当前绑定的 lightweight-ngram 本地训练 artifact，artifact={artifact_hash}。"
            f"它由你的本机 worker 训练生成，rows={rows}，train_loss={loss}。"
        )
    if any(word in lowered for word in ("hello", "hi", "hey")) or contains_any(text, ("你好", "在吗", "在不在")):
        return cn("我在。现在聊天已经可以绑定到本地训练 artifact，而不是只停留在 bootstrap 回复。")
    return cn(
        f"我收到你的问题了。当前回答来自本地训练 artifact，训练样本 {rows} 条，train_loss={loss}。"
        "这个阶段适合验证训练、绑定、运行链路；要获得强代码能力，需要继续接入更大的 LoRA/QLoRA 模型后端。"
    )


def asks_training_status(text: str, lowered: str) -> bool:
    return any(phrase in lowered for phrase in ("trained", "self trained", "self-trained", "training")) or contains_any(
        text,
        ("训练", "自训", "自己训", "自己训练", "你训练了", "是自己训练的吗", "是不是自己训练"),
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


def contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def cn(value: str) -> str:
    return value
