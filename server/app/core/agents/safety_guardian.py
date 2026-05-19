from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from server.app.core.generation.llm import OllamaClient
from server.app.utils.prompts import render_prompt


@dataclass(slots=True)
class SafetyAnalysis:
    mode: str
    risk_level: int
    reasoning: str
    message: str
    # Spec §32.2 compliant fields
    risk_confidence: float = 0.0
    risk_indicators: list[str] = field(default_factory=list)
    crisis_protocol_active: bool = False
    risk_level_label: str = "none"   # "none|low|medium|high|crisis"


_RISK_LABEL_MAP = {0: "none", 1: "low", 2: "medium", 3: "high", 4: "crisis", 5: "crisis"}


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
            return SafetyAnalysis(
                mode="normal", risk_level=0, reasoning="LLM unavailable", message="",
                risk_confidence=0.0, risk_indicators=[], crisis_protocol_active=False,
                risk_level_label="none",
            )

        try:
            raw = result.text.strip()
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
            data = json.loads(raw)

            rl = int(data.get("risk_level", 0))
            label = _RISK_LABEL_MAP.get(rl, "none")
            indicators = list(data.get("risk_indicators", []))
            confidence = float(data.get("risk_confidence", 0.85 if rl >= 3 else 0.5))

            return SafetyAnalysis(
                mode=data.get("mode", "normal"),
                risk_level=rl,
                reasoning=data.get("reasoning", ""),
                message=data.get("suggested_message", ""),
                risk_confidence=confidence,
                risk_indicators=indicators,
                crisis_protocol_active=(rl >= 4),
                risk_level_label=label,
            )
        except Exception:
            return SafetyAnalysis(
                mode="normal", risk_level=0, reasoning="Parsing failed", message="",
                risk_confidence=0.0, risk_indicators=[], crisis_protocol_active=False,
                risk_level_label="none",
            )
