from __future__ import annotations

import pytest

from server.app.core.agents.conversation_state import conversation_state_engine
from server.app.core.agents.phase_manager import PhaseManager
from server.app.models.sql.models import ChatSession


pytestmark = [pytest.mark.unit]


def test_conversation_state_engine_scores_change_talk() -> None:
    score = conversation_state_engine.score_change_talk("I want to try a different routine this week.")

    assert score > 0.3


def test_conversation_state_engine_builds_history_topics_and_agenda() -> None:
    state = conversation_state_engine.build_state(
        user_message="I want to change this",
        session_history=[
            {"role": "user", "content": "Let's talk about sleep", "route": "topic:burnout_sleep", "intent": "support", "safety_mode": "normal"},
            {"role": "assistant", "content": "Tell me more", "route": "topic:burnout_sleep", "intent": "support", "safety_mode": "normal"},
        ],
        structured_memory={"last_session_topic": "burnout_sleep", "recurring_themes": [{"theme": "sleep", "count": 2, "last_seen": "2026-05-17"}]},
        current_topic="burnout_sleep",
        turn_count=4,
    )

    assert state["primary_concern"] == "burnout_sleep"
    assert state["session_phase"] == 2
    assert "burnout_sleep" in state["explored_topics"]


def test_phase_manager_advances_to_phase_three_on_change_talk() -> None:
    manager = PhaseManager()
    session = ChatSession(user_id=1, title="Test", status="active")

    decision = manager.apply(session, {"primary_concern": "stress", "change_talk_score": 0.7}, turn_count=5)

    assert decision.session_phase == 3
    assert session.session_phase == 3
    assert session.insight_triggered is True


def test_phase_manager_marks_closure_when_requested() -> None:
    manager = PhaseManager()
    session = ChatSession(user_id=1, title="Test", status="active")

    decision = manager.apply(session, {"primary_concern": "stress", "closure_confirmed": True}, turn_count=2)

    assert decision.session_phase == 4
    assert session.closure_confirmed is True
