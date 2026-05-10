from __future__ import annotations

import json
import re
from dataclasses import dataclass

from server.app.core.generation.llm import OllamaClient
from server.app.utils.prompts import render_prompt


@dataclass(slots=True)
class SafetyAnalysis:
    mode: str
    risk_level: int
    reasoning: str
    message: str


class SafetyGuardian:
    """
    Agentic safety layer that uses LLM reasoning to detect nuanced clinical risks
    that keyword-based filters might miss.
    """

    def __init__(self, llm: OllamaClient | None = None) -> None:
        self.llm = llm or OllamaClient()

    def analyze(self, text: str) -> SafetyAnalysis:
        prompt = render_prompt("agents.safety_guardian", TEXT=text)
        result = self.llm.generate(prompt, temperature=0.1)
        if not result.available:
            return SafetyAnalysis("normal", 0, "LLM unavailable", "")

        try:
            raw = result.text.strip()
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
            data = json.loads(raw)

            return SafetyAnalysis(
                mode=data.get("mode", "normal"),
                risk_level=int(data.get("risk_level", 0)),
                reasoning=data.get("reasoning", ""),
                message=data.get("suggested_message", ""),
            )
        except Exception:
            return SafetyAnalysis("normal", 0, "Parsing failed", "")
