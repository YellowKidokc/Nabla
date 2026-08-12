from __future__ import annotations

import json
import urllib.request
from typing import Any


class LocalModelAdapter:
    """Adapter for a private local NLP service; no cloud fallback is implicit."""

    def __init__(self, endpoint: str = "http://localhost:8700/analyze", timeout: int = 30) -> None:
        self.endpoint = endpoint
        self.timeout = timeout

    def analyze(self, packet: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(packet).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            return {"lane": "local_nlp", "status": "blocked", "refusal_state": "service_unavailable",
                    "detail": type(exc).__name__}
        result.setdefault("lane", "local_nlp")
        result.setdefault("status", "candidate")
        return result
