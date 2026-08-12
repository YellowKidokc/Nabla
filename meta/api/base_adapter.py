from __future__ import annotations

import json
import os
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AdapterResult:
    provider: str
    model: str
    content: str
    raw: dict[str, Any]


class BaseAdapter(ABC):
    provider = "base"
    env_key = ""

    def __init__(self, model: str, timeout: int = 120) -> None:
        self.model = model
        self.timeout = timeout

    def api_key(self) -> str:
        value = os.environ.get(self.env_key, "").strip()
        if not value:
            raise RuntimeError(f"{self.env_key} is not set")
        return value

    @abstractmethod
    def analyze(self, system: str, prompt: str) -> AdapterResult:
        raise NotImplementedError

    def _post(self, url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", **headers},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))


class OpenAICompatibleAdapter(BaseAdapter):
    endpoint = ""

    def analyze(self, system: str, prompt: str) -> AdapterResult:
        raw = self._post(
            self.endpoint,
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
                "response_format": {"type": "json_object"},
            },
            {"Authorization": f"Bearer {self.api_key()}"},
        )
        return AdapterResult(self.provider, self.model, raw["choices"][0]["message"]["content"], raw)
