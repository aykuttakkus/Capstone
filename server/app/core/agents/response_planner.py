from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ResponsePlan:
    intent: str
    topic: str
    risk_mode: str
    knowledge_need: bool
    memory_need: bool
    tone_plan: str
    support_goal: str
    recommended_structure: str
    source_mode: str
    personalization_signals: list[str] = field(default_factory=list)
    risk_level: str = "none"
    risk_confidence: float = 0.0
    subtle_distress: bool = False
    primary_intent: str = ""
    secondary_intents: list[str] = field(default_factory=list)
    intent_confidence: float = 0.5
    needs_rag: bool = False
    retrieval_confidence: float = 0.0
    response_mode: str = "support"
    tone: str = "warm"
    ask_question: bool = True
    max_questions: int = 1
    diagnosis_allowed: bool = False
    medication_advice_allowed: bool = False
    source_required: bool = False
    boundary_required: bool = True
    escalation_required: bool = False

    def __post_init__(self) -> None:
        if not self.primary_intent:
            self.primary_intent = self.intent
        if not self.needs_rag:
            self.needs_rag = self.knowledge_need
        if self.risk_level == "none" and self.risk_mode not in {"normal", ""}:
            self.risk_level = "high"
        if self.source_required is False:
            self.source_required = self.source_mode in {"grounded", "knowledge_only", "knowledge_plus_memory"}


class ResponsePlanner:
    def build(
        self,
        *,
        intent: str,
        topic: str,
        safety_mode: str,
        profile_snapshot: str,
        mood_summary: str,
        journal_summary: str,
        recent_memory_count: int,
    ) -> ResponsePlan:
        if safety_mode != "normal":
            return ResponsePlan(
                intent=intent,
                topic=topic,
                risk_mode=safety_mode,
                knowledge_need=False,
                memory_need=False,
                tone_plan="urgent_supportive",
                support_goal="safety_stabilization",
                recommended_structure="safety_first",
                source_mode="safety_override",
                personalization_signals=[],
                risk_level="crisis" if safety_mode in {"crisis", "crisis_support"} else "high",
                risk_confidence=0.9,
                primary_intent="crisis" if safety_mode in {"crisis", "crisis_support"} else intent,
                intent_confidence=0.9,
                needs_rag=False,
                response_mode="crisis" if safety_mode in {"crisis", "crisis_support"} else "off_scope",
                tone="safety-focused",
                ask_question=safety_mode not in {"crisis", "crisis_support"},
                max_questions=1,
                source_required=False,
                escalation_required=True,
            )

        signals: list[str] = []
        tone_plan = "balanced"
        support_goal = "grounded_psychoeducation"
        source_mode = "knowledge_only"
        memory_need = recent_memory_count > 0 or bool(profile_snapshot)
        knowledge_need = True

        if profile_snapshot:
            signals.append("profile")
            source_mode = "knowledge_plus_memory"
        if recent_memory_count > 0:
            signals.append("memory")
        if mood_summary:
            signals.append("mood_trend")
            tone_plan = "gentle_and_pattern_aware"
        if journal_summary:
            signals.append("journal")
            source_mode = "knowledge_plus_memory"
        if "Emotional_Support" in profile_snapshot:
            tone_plan = "warm_supportive"
        if "Direct_and_Practical" in profile_snapshot:
            tone_plan = "direct_practical"
        if "Practical_Coping_Steps" in profile_snapshot:
            support_goal = "actionable_support"

        return ResponsePlan(
            intent=intent,
            topic=topic,
            risk_mode=safety_mode,
            knowledge_need=knowledge_need,
            memory_need=memory_need,
            tone_plan=tone_plan,
            support_goal=support_goal,
            recommended_structure="reflect_ground_explain_next_step",
            source_mode=source_mode,
            personalization_signals=signals,
            primary_intent=intent,
            needs_rag=knowledge_need,
            response_mode=_response_mode_for_intent(intent),
            tone=tone_plan,
            ask_question=True,
            max_questions=1,
            source_required=knowledge_need,
        )


response_planner = ResponsePlanner()


def _response_mode_for_intent(intent: str) -> str:
    return {
        "emotional_support": "support",
        "psychoeducation": "education",
        "coping_strategy": "coping",
        "symptom_exploration": "symptom_exploration",
        "clarification_needed": "clarify",
        "crisis": "crisis",
        "off_scope": "off_scope",
        "repair": "repair",
    }.get(intent, "support")
