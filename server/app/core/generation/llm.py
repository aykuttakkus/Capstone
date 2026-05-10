from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, request

from server.app.core.config import OLLAMA_BASE_URL, OLLAMA_MODEL


@dataclass(slots=True)
class LLMResult:
    text: str
    available: bool


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, prompt: str, temperature: float = 0.2) -> LLMResult:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }

        req = request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
            return LLMResult(text=str(body.get("response", "")).strip(), available=True)
        except (error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return LLMResult(text="", available=False)
