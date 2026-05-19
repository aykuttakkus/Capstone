from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from server.app.core.pipeline.risk_state import RiskState


@dataclass(slots=True)
class StructuredMemory:
    """Spec §31 compliant session memory structure."""
    main_concern: str = ""
    emotional_state: str = ""
    triggers: list[str] = field(default_factory=list)
    coping_tried: list[str] = field(default_factory=list)
    coping_effectiveness: dict[str, str] = field(default_factory=dict)
    user_goal: str = ""
    risk_state: dict[str, Any] = field(default_factory=dict)
    last_response_mode: str = ""
    important_new_information: list[str] = field(default_factory=list)


@dataclass(slots=True)
class MemoryUpdateResult:
    """Output contract per spec §32.9."""
    updated_session_summary: dict[str, Any]
    updated_risk_state: dict[str, Any]
    memory_update_notes: list[str] = field(default_factory=list)


_CONCERN_MAP = {
    "anxiety": ["anxious", "anxiety", "worried", "panic", "kaygı", "endişe"],
    "depression": ["depressed", "sad", "low mood", "hopeless", "üzgün", "mutsuz"],
    "stress": ["stressed", "overwhelmed", "pressure", "stres", "bunalmış"],
    "sleep": ["sleep", "insomnia", "can't sleep", "uyku", "uyuyamıyorum"],
    "relationships": ["relationship", "family", "friend", "partner", "aile", "arkadaş"],
    "self_esteem": ["worthless", "failure", "ashamed", "değersiz", "başarısız"],
    "trauma": ["trauma", "abuse", "assault", "travma"],
}

_TRIGGER_MAP = {
    "exam_stress": ["exam", "final", "test", "grade", "sınav", "not"],
    "work_pressure": ["work", "job", "deadline", "boss", "iş", "çalış"],
    "family_conflict": ["family", "parent", "mother", "father", "aile", "anne", "baba"],
    "sleep_issues": ["sleep", "insomnia", "nighttime", "uyku", "gece"],
    "social_anxiety": ["social", "people", "crowd", "alone", "yalnız", "insanlar"],
    "financial_stress": ["money", "debt", "financial", "para", "borç"],
}

_STRATEGY_MAP = {
    "breathing": ["breathing", "breath", "inhale", "exhale", "nefes"],
    "grounding": ["grounding", "5-4-3-2-1", "senses", "topraklanma"],
    "journaling": ["journal", "write down", "writing", "günlük", "yaz"],
    "sleep_routine": ["sleep routine", "bedtime routine", "uyku rutini"],
    "mindfulness": ["mindfulness", "meditation", "present moment", "farkındalık"],
    "physical_activity": ["exercise", "walk", "run", "yürüyüş", "egzersiz"],
}


class MemoryUpdater:
    """
    Pipeline Step 14: structured session memory update per spec §31 & §32.9.
    """

    def update(
        self,
        *,
        user_message: str,
        final_response: str,
        previous_session_summary: dict[str, Any],
        previous_risk_state: RiskState,
        response_mode: str,
        distress_signals: list[str],
    ) -> MemoryUpdateResult:
        notes: list[str] = []
        summary = dict(previous_session_summary)

        # 1. main_concern
        if not summary.get("main_concern"):
            concern = self._extract_concern(user_message)
            if concern:
                summary["main_concern"] = concern
                notes.append(f"main_concern set: {concern}")

        # 2. emotional_state from distress signals
        if distress_signals:
            state = self._signals_to_state(distress_signals)
            summary["emotional_state"] = state
            notes.append(f"emotional_state: {state}")
        elif not summary.get("emotional_state"):
            summary["emotional_state"] = "neutral"

        # 3. triggers — accumulate, deduplicate, cap at 10
        new_triggers = self._extract_triggers(user_message)
        existing_triggers: list[str] = list(summary.get("triggers") or [])
        for t in new_triggers:
            if t not in existing_triggers:
                existing_triggers.append(t)
        summary["triggers"] = existing_triggers[:10]

        # 4. coping_tried — from response content
        new_strategies = self._extract_strategies_from_response(final_response)
        existing_strats: list[str] = list(summary.get("coping_tried") or [])
        for s in new_strategies:
            if s not in existing_strats:
                existing_strats.append(s)
        summary["coping_tried"] = existing_strats[:15]

        # 5. coping_effectiveness — check for "didn't help" signals
        effectiveness = dict(summary.get("coping_effectiveness") or {})
        lowered_msg = user_message.lower()
        for strategy in existing_strats:
            if any(phrase in lowered_msg for phrase in ["didn't help", "not working", "doesn't work", "işe yaramıyor"]):
                effectiveness[strategy] = "not helpful"
        summary["coping_effectiveness"] = effectiveness

        # 6. user_goal
        if not summary.get("user_goal"):
            goal = self._extract_goal(user_message)
            if goal:
                summary["user_goal"] = goal
                notes.append(f"user_goal: {goal}")

        # 7. last_response_mode
        summary["last_response_mode"] = response_mode

        # 8. important_new_information
        new_info = self._extract_new_info(user_message, summary)
        existing_info: list[str] = list(summary.get("important_new_information") or [])
        for info in new_info:
            if info not in existing_info:
                existing_info.append(info)
        summary["important_new_information"] = existing_info[-5:]

        # 9. risk_state snapshot
        updated_risk: dict[str, Any] = {
            "current_risk_level": previous_risk_state.current_risk_level,
            "crisis_protocol_active": previous_risk_state.crisis_protocol_active,
            "needs_human_support": previous_risk_state.needs_human_support,
            "cumulative_risk_signals": list(previous_risk_state.cumulative_risk_signals[-10:]),
        }
        summary["risk_state"] = updated_risk

        return MemoryUpdateResult(
            updated_session_summary=summary,
            updated_risk_state=updated_risk,
            memory_update_notes=notes,
        )

    def _extract_concern(self, message: str) -> str:
        lowered = message.lower()
        for concern, keywords in _CONCERN_MAP.items():
            if any(kw in lowered for kw in keywords):
                return concern
        return ""

    def _signals_to_state(self, signals: list[str]) -> str:
        if not signals:
            return "neutral"
        if "hopelessness" in signals or "goodbye" in signals:
            return "severely distressed"
        if "burden" in signals or "helplessness" in signals:
            return "distressed"
        if "shame" in signals or "withdrawal" in signals:
            return "struggling"
        return "mild distress"

    def _extract_triggers(self, message: str) -> list[str]:
        lowered = message.lower()
        return [name for name, kws in _TRIGGER_MAP.items() if any(kw in lowered for kw in kws)]

    def _extract_strategies_from_response(self, response: str) -> list[str]:
        lowered = response.lower()
        return [s for s, kws in _STRATEGY_MAP.items() if any(kw in lowered for kw in kws)]

    def _extract_goal(self, message: str) -> str:
        lowered = message.lower()
        if any(w in lowered for w in ["want to feel", "want to be", "want to stop", "hissetmek istiyorum"]):
            return "symptom relief"
        if any(w in lowered for w in ["better sleep", "daha iyi uyku"]):
            return "improve sleep"
        if any(w in lowered for w in ["manage", "cope", "handle", "başa çık"]):
            return "coping skills"
        return ""

    def _extract_new_info(self, message: str, current_summary: dict[str, Any]) -> list[str]:
        info: list[str] = []
        lowered = message.lower()
        existing = list(current_summary.get("important_new_information") or [])

        if any(kw in lowered for kw in ["therapist", "psychiatrist", "counselor", "professional", "terapist", "psikiyatrist"]):
            if "professional_support_mentioned" not in existing:
                info.append("professional_support_mentioned")

        if any(kw in lowered for kw in ["medication", "medicine", "drug", "pill", "ilaç"]):
            if "medication_mentioned" not in existing:
                info.append("medication_mentioned")

        if any(kw in lowered for kw in ["suicid", "kill myself", "end my life", "intihar"]):
            if "suicidal_ideation_mentioned" not in existing:
                info.append("suicidal_ideation_mentioned")

        if any(kw in lowered for kw in ["abuse", "hurt me", "hitting", "istismar"]):
            if "abuse_mentioned" not in existing:
                info.append("abuse_mentioned")

        return info
