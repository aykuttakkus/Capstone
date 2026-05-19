from __future__ import annotations

import pytest

from server.app.core.agents.orchestrator import OrchestrationPlan
from server.app.core.agents.response_planner import ResponsePlanner
from server.app.models.schemas.chat import ChatResponse


pytestmark = [pytest.mark.unit]


def test_chat_response_exposes_phase0_contract_defaults() -> None:
    response = ChatResponse(
        session_id=1,
        status="grounded",
        route="topic:stress_anxiety",
        intent="general_query",
        safety_mode="normal",
        summary="ok",
        answer="Hello",
    )

    assert response.confidence == 0.0
    assert response.evidence_status == "unknown"
    assert response.conversation_mode == "answer"
    assert response.supporting_chunks == []
    assert response.hallucination_guard.blocked_claims == []


def test_orchestration_plan_includes_routing_metadata_defaults() -> None:
    plan = OrchestrationPlan(
        route="topic:stress_anxiety",
        topic="stress_anxiety",
        intent="general_query",
        safety_mode="normal",
        risk_level=0,
    )

    assert plan.retrieval_need is False
    assert plan.evidence_need is False
    assert plan.should_clarify is False
    assert plan.conversation_mode == "answer"
    assert plan.confidence == 0.5


def test_response_planner_marks_informational_requests_as_explain_mode() -> None:
    planner = ResponsePlanner()
    plan = planner.build(
        intent="educational_request",
        topic="stress_anxiety",
        safety_mode="normal",
        profile_snapshot="",
        mood_summary="",
        journal_summary="",
        recent_memory_count=0,
        confidence=0.82,
    )

    assert plan.retrieval_need is True
    assert plan.evidence_need is True
    assert plan.conversation_mode == "explain"
    assert plan.confidence == 0.82
