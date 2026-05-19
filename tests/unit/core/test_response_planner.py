from __future__ import annotations

from server.app.core.agents.response_planner import ResponsePlanner, ResponsePlan


def test_response_plan_keeps_backward_compatible_fields() -> None:
    plan = ResponsePlan(
        intent="psychoeducation",
        topic="stress_anxiety",
        risk_mode="normal",
        knowledge_need=True,
        memory_need=False,
        tone_plan="balanced",
        support_goal="grounded_psychoeducation",
        recommended_structure="reflect_ground_explain_next_step",
        source_mode="grounded",
    )

    assert plan.primary_intent == "psychoeducation"
    assert plan.needs_rag is True
    assert plan.source_required is True
    assert plan.max_questions == 1
    assert plan.diagnosis_allowed is False
    assert plan.medication_advice_allowed is False


def test_response_planner_builds_crisis_contract() -> None:
    planner = ResponsePlanner()

    plan = planner.build(
        intent="crisis",
        topic="help_seeking",
        safety_mode="crisis_support",
        profile_snapshot="",
        mood_summary="",
        journal_summary="",
        recent_memory_count=0,
    )

    assert plan.response_mode == "crisis"
    assert plan.tone == "safety-focused"
    assert plan.needs_rag is False
    assert plan.escalation_required is True
    assert plan.source_required is False


def test_response_planner_builds_normal_contract() -> None:
    planner = ResponsePlanner()

    plan = planner.build(
        intent="coping_strategy",
        topic="stress_anxiety",
        safety_mode="normal",
        profile_snapshot="Direct_and_Practical",
        mood_summary="anxiety elevated",
        journal_summary="",
        recent_memory_count=2,
    )

    assert plan.primary_intent == "coping_strategy"
    assert plan.response_mode == "coping"
    assert plan.needs_rag is True
    assert plan.source_required is True
    assert plan.max_questions == 1
    assert plan.boundary_required is True
    assert "profile" in plan.personalization_signals
    assert "memory" in plan.personalization_signals
