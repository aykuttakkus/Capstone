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
        )


response_planner = ResponsePlanner()
