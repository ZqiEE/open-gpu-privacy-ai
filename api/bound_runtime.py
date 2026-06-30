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
        if backend_kind in {"jsonl-stat", "checkpoint-artifact"}:
            answer = self._chat_checkpoint_summary(prompt, backend_ref, binding)
            return {"answer": answer, "source": "artifact-bound-checkpoint", "binding": binding}
        raise BoundRuntimeUnavailable("unsupported artifact binding backend: " + backend_kind)

    def _chat_checkpoint_summary(self, prompt: str, backend_ref: str, binding: dict[str, Any]) -> str:
        path = resolve_local_ref(backend_ref)
        checkpoint = None
        if path and path.exists() and path.is_file():
            try:
                checkpoint = json.loads(path.read_bytes().decode("utf-8"))
            except Exception:
                checkpoint = {"checkpoint_path": str(path)}
        if checkpoint:
            return build_checkpoint_bound_answer(prompt, binding, checkpoint)
        raise BoundRuntimeUnavailable("binding has no loadable local checkpoint: " + str(backend_ref))

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


def build_checkpoint_bound_answer(prompt: str, binding: dict[str, Any], checkpoint: dict[str, Any]) -> str:
    text = prompt.strip()
    lowered = text.lower()
    model_key = binding.get("model_key") or "ailovanta-owned:candidate"
    artifact_hash = binding.get("artifact_hash") or "local-artifact"
    backend = checkpoint.get("backend") or binding.get("backend_kind") or "checkpoint-artifact"

    if not text:
        return zh("我在。你可以直接输入问题，我会按当前 Ailovanta 本地运行环境回答。")

    if asks_training_status(text, lowered):
        return zh(
            "直接说：当前聊天不是一个已经完整自训练出来的大模型。"
            "现在能回答，是因为 Ailovanta 的 owned runtime、路由、artifact 绑定和本地 bootstrap 响应器已经接通。"
            "真正的自训练模型权重还在下一阶段接入：自动取数、生成训练任务、验证样本、训练/蒸馏、产出 checkpoint，再绑定到 runtime。"
        )

    if asks_model_identity(text, lowered):
        return zh(
            "我是 Ailovanta 本地 owned runtime 的 bootstrap 助手，不是 OpenAI、Claude、Gemini 之类的外部大模型。"
            f"当前绑定模型标识是 {model_key}，后端 artifact 是 {artifact_hash}，backend 是 {backend}。"
            "这代表自有运行链路已接通，但还不是最终训练完成的 foundation model。"
        )

    if asks_followup_pressure(text, lowered):
        return zh(
            "你问的是当前能力边界。答案是：链路是自己的，完整大模型还没训练完成。"
            "现在这一步先保证 app -> owned runtime -> artifact binding -> validation provenance 全部能跑；"
            "下一步才把 core 训练产物接进来，让回答由真实训练 checkpoint 驱动。"
        )

    if any(word in lowered for word in ("hello", "hi", "hey")) or contains_any(text, ("你好", "在吗", "在不在")):
        return zh("我在。Ailovanta 本地 owned runtime 已经接通，你可以继续问我问题。")

    if text in {"啥", "什么", "?", "？"} or lowered in {"what", "what?"}:
        return zh(
            "你刚才看到的是本地 owned runtime 的启动响应。"
            "现在这条链路已经从 fallback 切到 Ailovanta 自己的 runtime，可以继续测试聊天、Dashboard 和 API Docs。"
        )

    if any(word in lowered for word in ("status", "runtime", "checkpoint")) or contains_any(text, ("状态", "运行", "检查点")):
        return zh(f"当前走的是 Ailovanta owned runtime，本地绑定模型是 {model_key}，artifact 是 {artifact_hash}。路由、绑定、验证链路已接通。")

    return zh(
        "我收到你的问题了。当前本地版本会先给出 owned runtime bootstrap 回答。"
        "如果你问的是模型能力边界：它现在不是完整自训练大模型，下一步要接入 core 训练产物和真实模型后端。"
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


def asks_followup_pressure(text: str, lowered: str) -> bool:
    return lowered in {"answer me", "tell me", "say it"} or contains_any(text, ("我问你呢", "直接回答", "别绕", "说清楚"))


def contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def zh(value: str) -> str:
    return value
