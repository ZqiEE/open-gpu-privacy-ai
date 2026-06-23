from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass
class OllamaConfig:
    base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    timeout_seconds: float = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "30"))


class OllamaUnavailable(RuntimeError):
    pass


class OllamaAdapter:
    def __init__(self, config: OllamaConfig | None = None) -> None:
        self.config = config or OllamaConfig()

    def chat(self, prompt: str, mode: str = "open", memory: list[str] | None = None) -> str:
        system = self._system_prompt(mode, memory or [])
        payload = {
            "model": self.config.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
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
    def _system_prompt(mode: str, memory: list[str]) -> str:
        memory_text = "\n".join(f"- {item}" for item in memory[-8:]) or "No stored memory."
        return (
            "You are Ailovanta, an AI assistant inside a local distributed compute MVP. "
            "Answer directly and practically. "
            f"Current mode: {mode}.\n"
            f"Local user memory:\n{memory_text}\n"
            "Focus on AI runtime, distributed compute, node networks, training orchestration, and developer execution."
        )
