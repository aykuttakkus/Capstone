from __future__ import annotations

import json
import re

from server.app.core.generation.llm import OllamaClient
from server.app.services.flows.topics import TOPIC_KEYWORDS
from server.app.utils.text import contains_any, normalize_text
from server.app.utils.prompts import render_prompt


class LlmMetadataClassifier:
    """
    Uses the local LLM to evaluate a text chunk and assign
    it a relevant predefined topic and extract keywords.
    """

    def __init__(self, ollama_client: OllamaClient | None = None) -> None:
        self.llm = ollama_client or OllamaClient()
        self.allowed_topics = [
            "stress_anxiety",
            "low_mood",
            "burnout_sleep",
            "social_pressure",
            "help_seeking",
            "general",
        ]

    def _heuristic_classify(self, text: str, title: str) -> dict[str, str | list[str]]:
        haystack = normalize_text(f"{title} {text}")
        for topic in ("burnout_sleep", "low_mood", "stress_anxiety", "social_pressure", "help_seeking"):
            keywords = TOPIC_KEYWORDS.get(topic, [])
            if contains_any(haystack, keywords):
                return {"topic": topic, "keywords": keywords[:5]}
        return {"topic": "general", "keywords": []}

    def classify(self, text: str, title: str) -> dict[str, str | list[str]]:
        snippet = text[:1500]
        default_prompt = (
            "Classify the following mental health text into one topic from: $TOPICS. "
            "Return ONLY strict JSON with keys topic and keywords. "
            "Topic must be one of the allowed topics.\n\n"
            "Title: $TITLE\n"
            "Text: $SNIPPET"
        )
        prompt = render_prompt(
            "ingestion.metadata_classifier",
            default=default_prompt,
            TOPICS=", ".join(self.allowed_topics),
            TITLE=title,
            SNIPPET=snippet,
        )
        result = self.llm.generate(prompt, temperature=0.1)
        if not result.available:
            return self._heuristic_classify(snippet, title)

        raw = result.text.strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()

        try:
            data = json.loads(raw)
            topic = data.get("topic", "general")
            if topic not in self.allowed_topics:
                return self._heuristic_classify(snippet, title)

            keywords = data.get("keywords", [])
            if not isinstance(keywords, list):
                keywords = [str(keywords)]

            return {"topic": topic, "keywords": keywords[:5]}
        except Exception:
            return self._heuristic_classify(snippet, title)
