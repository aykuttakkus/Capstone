from __future__ import annotations

import json
import re
from dataclasses import dataclass

from server.app.core.generation.llm import OllamaClient
from server.app.utils.prompts import render_prompt


@dataclass(slots=True)
class SentimentProfile:
    label: str
    urgency: int
    empathy_required: bool
    rationale: str


class SentimentAgent:
    """
    Analyzes user sentiment and emotional distress to personalize
    the assistant's tone and empathy level.
    """

    def __init__(self, llm: OllamaClient | None = None) -> None:
        self.llm = llm or OllamaClient()

    def analyze(self, text: str) -> SentimentProfile:
        prompt = render_prompt("agents.sentiment_agent", TEXT=text)
        result = self.llm.generate(prompt, temperature=0.1)
        if not result.available:
            return SentimentProfile("neutral", 1, False, "LLM unavailable")

        try:
            raw = result.text.strip()
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
            data = json.loads(raw)
            return SentimentProfile(
                label=data.get("label", "neutral"),
                urgency=int(data.get("urgency", 1)),
                empathy_required=data.get("empathy_required", False),
                rationale=data.get("rationale", ""),
            )
        except Exception:
            return SentimentProfile("neutral", 1, False, "Parsing failed")
