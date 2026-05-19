# DEPRECATED: Overlaps with Context Manager (§4) spec. Unused in current pipeline.
# Some fields may be useful for Phase 2 refactoring; audit before final deletion.
# Kept for compatibility only.
# TODO: Audit and consolidate with Context Manager in Phase 2

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


CHANGE_TALK_MARKERS = [
    "i want",
    "i would like",
    "i can try",
    "i could",
    "ready to",
    "want to change",
    "denemek istiyorum",
    "değiştirmek istiyorum",
]

RESISTANCE_MARKERS = [
    "don't want",
    "do not want",
    "not sure",
    "bilmiyorum",
    "boşver",
    "yok",
    "it won't help",
    "doesn't help",
]

AGENDA_MARKERS = ["work", "sleep", "family", "relationship", "school", "exam", "stress", "anxiety", "burnout"]


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _contains_any(text: str, markers: list[str]) -> bool:
    return any(marker in text for marker in markers)


@dataclass(slots=True)
class ConversationStateEngine:
    def score_change_talk(self, user_message: str) -> float:
        msg = _normalize(user_message)
        if not msg:
            return 0.0

        score = 0.0
        for marker in CHANGE_TALK_MARKERS:
            if marker in msg:
                score += 0.35
        if re.search(r"\b(try|might|could|can)\b", msg):
            score += 0.15
        if re.search(r"\b(want|would like|ready)\b", msg):
            score += 0.2
        return min(score, 1.0)

    def detect_resistance(self, user_message: str) -> bool:
        msg = _normalize(user_message)
        return _contains_any(msg, RESISTANCE_MARKERS) or msg.startswith("no ") or msg in {"no", "nah"}

    def _extract_topics(self, session_history: list[dict[str, str]], current_topic: str | None) -> list[str]:
        topics: list[str] = []
        if current_topic:
            topics.append(current_topic)
        for item in session_history:
            route = item.get("route", "")
            if route.startswith("topic:"):
                candidate = route.split(":", 1)[1].strip()
                if candidate and candidate not in topics:
                    topics.append(candidate)
        return topics

    def build_state(
        self,
        *,
        user_message: str,
        session_history: list[dict[str, str]],
        structured_memory: dict[str, Any],
        current_topic: str | None,
        turn_count: int,
    ) -> dict[str, Any]:
        normalized_message = _normalize(user_message)
        change_talk_score = self.score_change_talk(user_message)
        resistance_detected = self.detect_resistance(user_message)
        explored_topics = self._extract_topics(session_history, current_topic)

        change_talk_statements = [
            item["content"]
            for item in session_history
            if _contains_any(_normalize(item.get("content", "")), CHANGE_TALK_MARKERS)
        ]
        if _contains_any(normalized_message, CHANGE_TALK_MARKERS):
            change_talk_statements.append(user_message)

        agenda_set = bool(explored_topics) and turn_count >= 4
        primary_concern = structured_memory.get("last_session_topic") or current_topic
        unexplored_mentions = [
            topic
            for topic in structured_memory.get("recurring_themes", [])
            if isinstance(topic, dict) and topic.get("theme") and topic.get("theme") not in explored_topics
        ]

        distress_level = 3
        if _contains_any(normalized_message, ["can't take it", "artık dayanamıyorum", "end it", "what's the point"]):
            distress_level = 9
        elif _contains_any(normalized_message, ["so stressed", "anxious", "panic", "overwhelmed", "korkuyorum"]):
            distress_level = 7

        return {
            "primary_concern": primary_concern,
            "explored_topics": explored_topics,
            "unexplored_mentions": unexplored_mentions,
            "change_talk_score": round(change_talk_score, 2),
            "change_talk_statements": change_talk_statements,
            "resistance_detected": resistance_detected,
            "distress_level": distress_level,
            "stuck_in_problem": any(term in normalized_message for term in ["bilmiyorum", "stuck", "same", "always"]),
            "cannot_envision_change": len(normalized_message.split()) < 5,
            "session_phase": 1 if turn_count < 4 else 2 if turn_count < 8 else 3,
            "agenda_set": agenda_set,
            "sustain_talk_ratio": 0.0 if not session_history else round(
                sum(1 for item in session_history if _contains_any(_normalize(item.get("content", "")), ["can't", "don't", "won't", "yapamam", "istemiyorum"]))
                / len(session_history),
                2,
            ),
        }


conversation_state_engine = ConversationStateEngine()
