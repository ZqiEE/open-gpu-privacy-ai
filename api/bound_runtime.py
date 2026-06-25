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
    token_count = checkpoint.get("token_count") or checkpoint.get("metrics", {}).get("token_count")
    train_loss = checkpoint.get("train_loss")
    eval_loss = checkpoint.get("eval_loss")
    backend = checkpoint.get("backend") or binding.get("backend_kind")
    return (
        "已加载该模型绑定的本地 checkpoint 元数据。"
        f"\n模型：{binding.get('model_key')}"
        f"\n后端：{backend}"
        f"\nArtifact：{binding.get('artifact_hash')}"
        f"\nToken count：{token_count}"
        f"\nTrain loss：{train_loss}"
        f"\nEval loss：{eval_loss}"
        "\n当前 checkpoint 不是完整可对话权重大模型时，只返回绑定与训练产物状态，不伪装成真实生成模型。"
        f"\n用户输入：{prompt}"
    )
