from __future__ import annotations

from .base_adapter import AdapterResult, BaseAdapter


class ClaudeAdapter(BaseAdapter):
    provider = "claude"
    env_key = "ANTHROPIC_API_KEY"
    endpoint = "https://api.anthropic.com/v1/messages"

    def __init__(self, model: str = "claude-sonnet-4-5", timeout: int = 120) -> None:
        super().__init__(model, timeout)

    def analyze(self, system: str, prompt: str) -> AdapterResult:
        raw = self._post(
            self.endpoint,
            {"model": self.model, "max_tokens": 8192, "temperature": 0,
             "system": system, "messages": [{"role": "user", "content": prompt}]},
            {"x-api-key": self.api_key(), "anthropic-version": "2023-06-01"},
        )
        content = "".join(block.get("text", "") for block in raw.get("content", []))
        return AdapterResult(self.provider, self.model, content, raw)
