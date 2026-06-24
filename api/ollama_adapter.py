from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass
class OllamaConfig:
    base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    timeout_seconds: float = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "30"))


class OllamaUnavailable(RuntimeError):
    pass


class OllamaAdapter:
    """Temporary local bootstrap model adapter for the public MVP."""

    def __init__(self, config: OllamaConfig | None = None) -> None:
        self.config = config or OllamaConfig()

    def chat(self, prompt: str, mode: str = "open", memory: list[str] | None = None) -> str:
        return self.chat_messages([{"role": "user", "content": prompt}], mode=mode, memory=memory)

    def chat_messages(self, messages: list[dict], mode: str = "open", memory: list[str] | None = None) -> str:
        system = self._system_prompt(mode, memory or [])
        clean_messages = self._clean_messages(messages)
        if not any(message["role"] == "user" for message in clean_messages):
            raise OllamaUnavailable("at least one user message is required")
        payload = {
            "model": self.config.model,
            "stream": False,
            "messages": [{"role": "system", "content": system}, *clean_messages],
        }
        try:
            with httpx.Client(timeout=self.config.timeout_seconds) as client:
                response = client.post(f"{self.config.base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:  # local runtime should degrade gracefully
            raise OllamaUnavailable(str(exc)) from exc

        message = data.get("message") or {}
        content = message.get("content")
        if not content:
            raise OllamaUnavailable("empty Ollama response")
        return content

    @staticmethod
    def _clean_messages(messages: list[dict]) -> list[dict]:
        clean = []
        for message in messages:
            role = str(message.get("role", "")).strip()
            content = str(message.get("content", "")).strip()
            if role in {"user", "assistant", "system"} and content:
                clean.append({"role": role, "content": content})
        return clean

    @staticmethod
    def _system_prompt(mode: str, memory: list[str]) -> str:
        memory_text = "\n".join(f"- {item}" for item in memory[-8:]) or "No stored memory."
        return (
            "You are Ailovanta, an AI assistant inside a local distributed compute MVP. "
            "Answer directly and practically. "
            "Model boundary: current inference may be served by a temporary local bootstrap model through Ollama. "
            "Ailovanta-owned foundation model status depends on verified runtime manifests promoted from core training artifacts. "
            f"Current mode: {mode}.\n"
            f"Local user memory:\n{memory_text}\n"
            "Focus on AI runtime, distributed compute, node networks, training orchestration, and developer execution. "
            "Use the provided conversation history when answering follow-up questions."
        )
