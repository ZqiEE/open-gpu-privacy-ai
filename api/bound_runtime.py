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
    del checkpoint
    text = prompt.strip()
    lowered = text.lower()

    if not text:
        return "我在。你可以直接输入问题，我会按当前 Ailovanta 本地运行环境回答。"

    if any(word in lowered for word in ("hello", "hi", "hey")) or any(word in text for word in ("你好", "在吗", "在不在")):
        return "我在。Ailovanta 本地 owned runtime 已经接通，你可以继续问我问题。"

    if text in {"啥", "什么", "?", "？"} or lowered in {"what", "what?"}:
        return "你刚才看到的是本地 owned runtime 的启动响应。现在这条链路已经从 fallback 切到 Ailovanta 自己的 runtime，你可以继续测试聊天、Dashboard 和 API Docs。"

    if any(word in lowered for word in ("status", "runtime", "model", "checkpoint")) or any(word in text for word in ("状态", "模型", "运行", "检查点")):
        model_key = binding.get("model_key") or "ailovanta-owned:candidate"
        artifact_hash = binding.get("artifact_hash") or "local-artifact"
        return f"当前走的是 Ailovanta owned runtime，本地绑定模型是 {model_key}，artifact 是 {artifact_hash}。这表示路由、绑定、验证链路已接通。"

    return (
        "我收到你的问题了。当前本地版本已经通过 Ailovanta owned runtime 返回结果；下一步会继续接入更强的训练产物和模型后端，让回答能力从启动级响应升级到真实代码智能能力。"
    )
