from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from server.app.core.generation.llm import OllamaClient
from server.app.utils.prompts import render_prompt


@dataclass(slots=True)
class MemoryUpdateResult:
    updated_session_summary: dict[str, Any]
    updated_risk_state: Any
    memory_update_notes: list[str] = field(default_factory=list)


class MemoryAgent:
    """
    Episodic Memory agent that extracts and persists clinical insights from
    interactions to maintain continuity across sessions.
    """

    def __init__(self, llm: OllamaClient | None = None) -> None:
        self.llm = llm or OllamaClient()

    @staticmethod
    def empty() -> dict[str, Any]:
        return {
            "v": 2,
            "preferred_name": "",
            "recurring_themes": [],
            "user_vocabulary": [],
            "mood_trend": [],
            "last_session_topic": "",
            "last_session_date": date.today().isoformat(),
            "active_action_plan": "",
            "suggested_strategies": [],
            "unhelpful_strategies": [],
            "privacy_notes": [],
        }

    @classmethod
    def parse(cls, raw: str | None) -> dict[str, Any]:
        base = cls.empty()
        if not raw:
            return base

        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError:
            decoded = None

        if isinstance(decoded, dict):
            base.update(decoded)
        else:
            base["last_session_topic"] = str(raw).strip()[:160]
            base["recurring_themes"] = cls._themes_from_text(str(raw))

        base["v"] = 2
        base["recurring_themes"] = cls._normalize_themes(base.get("recurring_themes"))
        base["user_vocabulary"] = cls._dedupe_strings(base.get("user_vocabulary", []), limit=12)
        base["mood_trend"] = cls._normalize_mood_trend(base.get("mood_trend", []))
        base["suggested_strategies"] = cls._dedupe_strings(base.get("suggested_strategies", []), limit=16)
        base["unhelpful_strategies"] = cls._dedupe_strings(base.get("unhelpful_strategies", []), limit=16)
        base["privacy_notes"] = cls._dedupe_strings(base.get("privacy_notes", []), limit=8)
        base["last_session_date"] = str(base.get("last_session_date") or date.today().isoformat())
        return base

    @staticmethod
    def mood_trend_summary(memory: dict[str, Any]) -> str:
        values = MemoryAgent._normalize_mood_trend(memory.get("mood_trend", []))[-5:]
        if not values:
            return "Mood trend unavailable."
        direction = "stable"
        if len(values) >= 2 and values[-1] > values[0]:
            direction = "improving"
        elif len(values) >= 2 and values[-1] < values[0]:
            direction = "declining"
        return f"Mood trend recent: {values} ({direction})."

    def summarize_interaction(
        self,
        user_msg: str,
        ai_msg: str,
        current_memory: str = "",
        mood_score: int | None = None,
    ) -> str:
        current = self.parse(current_memory)
        prompt = render_prompt(
            "agents.memory_agent",
            CURRENT_MEMORY=current_memory,
            USER_MSG=user_msg,
            AI_MSG=ai_msg,
        )
        result = self.llm.generate(prompt, temperature=0.1)
        if not result.available:
            return json.dumps(self._fallback_update(current, user_msg, ai_msg, mood_score), ensure_ascii=False)

        updated = self.parse(result.text.strip())
        merged = self._merge_memory(current, updated)
        merged = self._fallback_update(merged, user_msg, ai_msg, mood_score)
        return json.dumps(merged, ensure_ascii=False)

    @staticmethod
    def _themes_from_text(text: str) -> list[dict[str, Any]]:
        lowered = text.lower()
        candidates = {
            "stress": ["stress", "stres"],
            "sleep": ["sleep", "uyku", "insomnia"],
            "work": ["work", "job", "iş"],
            "loneliness": ["lonely", "alone", "yalnız"],
            "anxiety": ["anxiety", "anxious", "kaygı", "panic"],
            "burnout": ["burnout", "tüken"],
        }
        themes = []
        for theme, markers in candidates.items():
            if any(marker in lowered for marker in markers):
                themes.append({"theme": theme, "count": 1, "last_seen": date.today().isoformat()})
        if not themes and text.strip():
            themes.append({"theme": text.strip()[:48], "count": 1, "last_seen": date.today().isoformat()})
        return themes[:5]

    @staticmethod
    def _normalize_themes(value: object) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []
        normalized = []
        for item in value:
            if isinstance(item, dict):
                theme = str(item.get("theme", "")).strip()
                if not theme:
                    continue
                try:
                    count = int(item.get("count", 1))
                except (TypeError, ValueError):
                    count = 1
                normalized.append(
                    {
                        "theme": theme[:80],
                        "count": max(1, count),
                        "last_seen": str(item.get("last_seen") or date.today().isoformat()),
                    }
                )
            elif isinstance(item, str) and item.strip():
                normalized.append({"theme": item.strip()[:80], "count": 1, "last_seen": date.today().isoformat()})
        return normalized[:12]

    @staticmethod
    def _normalize_mood_trend(value: object) -> list[int]:
        if not isinstance(value, list):
            return []
        normalized = []
        for item in value:
            try:
                score = int(item)
            except (TypeError, ValueError):
                continue
            normalized.append(max(1, min(score, 10)))
        return normalized[-12:]

    @staticmethod
    def _dedupe_strings(value: object, limit: int) -> list[str]:
        if not isinstance(value, list):
            return []
        seen = []
        for item in value:
            text = str(item).strip()
            if text and text not in seen:
                seen.append(text[:120])
        return seen[:limit]

    def _fallback_update(
        self,
        memory: dict[str, Any],
        user_msg: str,
        ai_msg: str,
        mood_score: int | None,
    ) -> dict[str, Any]:
        updated = dict(memory)
        user_msg = self._filter_trauma_content(user_msg)
        themes = {item["theme"]: item for item in self._normalize_themes(updated.get("recurring_themes"))}
        for item in self._themes_from_text(user_msg):
            if item["theme"] in themes:
                themes[item["theme"]]["count"] += 1
                themes[item["theme"]]["last_seen"] = date.today().isoformat()
            else:
                themes[item["theme"]] = item
        updated["recurring_themes"] = list(themes.values())[:12]
        updated["last_session_topic"] = self._minimal_non_identifying_text(user_msg)
        updated["last_session_date"] = date.today().isoformat()
        if mood_score is not None:
            updated["mood_trend"] = self._normalize_mood_trend([*updated.get("mood_trend", []), mood_score])

        suggested = self._dedupe_strings(
            [*updated.get("suggested_strategies", []), *self._strategy_labels(ai_msg)],
            limit=16,
        )
        if suggested:
            updated["suggested_strategies"] = suggested
        unhelpful = self._dedupe_strings(
            [*updated.get("unhelpful_strategies", []), *self._unhelpful_strategy_labels(user_msg)],
            limit=16,
        )
        if unhelpful:
            updated["unhelpful_strategies"] = unhelpful

        if suggested:
            updated["active_action_plan"] = self._minimal_non_identifying_text(ai_msg)
        return updated

    @staticmethod
    def _strategy_labels(text: str) -> list[str]:
        lowered = text.lower()
        labels: list[str] = []
        patterns = {
            "breathing": ["breath", "breathing", "nefes"],
            "grounding": ["ground", "grounding", "5-4-3-2-1", "topraklan"],
            "journaling": ["journal", "write down", "günlük", "yaz"],
            "walking": ["walk", "walking", "yürüyüş"],
            "sleep_routine": ["sleep routine", "bedtime", "uyku rutini"],
            "trusted_person": ["trusted person", "someone you trust", "güvendiğin"],
        }
        for label, markers in patterns.items():
            if any(marker in lowered for marker in markers):
                labels.append(label)
        return labels

    @classmethod
    def _unhelpful_strategy_labels(cls, text: str) -> list[str]:
        lowered = text.lower()
        unhelpful_markers = [
            "didn't help",
            "did not help",
            "doesn't help",
            "not helpful",
            "işe yaramadı",
            "yardım etmedi",
        ]
        if not any(marker in lowered for marker in unhelpful_markers):
            return []
        return cls._strategy_labels(text)

    @staticmethod
    def _merge_memory(current: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
        merged = dict(current)
        for key, value in new.items():
            if value not in ("", [], None):
                merged[key] = value
        return merged

    _TRAUMA_KEYWORDS = [
        "suicide", "kill myself", "end my life", "hurt myself", "self-harm",
        "abuse", "assault", "rape", "attacked", "molested",
        "intihar", "kendime zarar", "istismar", "tecavüz",
    ]

    @classmethod
    def _filter_trauma_content(cls, text: str) -> str:
        """Replace verbatim trauma/crisis content with a semantic label to protect privacy."""
        lowered = text.lower()
        if any(kw in lowered for kw in cls._TRAUMA_KEYWORDS):
            return "[sensitive_content_redacted]"
        return text

    @staticmethod
    def _minimal_non_identifying_text(text: str) -> str:
        compact = " ".join(text.split())
        compact = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[email]", compact)
        compact = re.sub(r"\b\d{3,}\b", "[number]", compact)
        return compact[:180]
