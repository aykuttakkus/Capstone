from __future__ import annotations

from types import SimpleNamespace

import pytest

from server.app.services.memory_context import build_memory_bundle


pytestmark = [pytest.mark.unit]


def test_build_memory_bundle_combines_session_profile_and_recent_turns() -> None:
    bundle = build_memory_bundle(
        session_summary="Topic: stress_anxiety. Intent: confirmation.",
        user_memory="Preferred name: Aykut",
        profile_summary="Communication style: direct",
        mood_summary="recent: [4, 5]",
        journal_summary="journal: overwhelmed at work",
        recent_segments=[SimpleNamespace(content="User prefers short answers"), SimpleNamespace(content="Walks helped this week")],
        reflections=[SimpleNamespace(content="Previously suggested grounding helped" )],
        history=[
            {"role": "user", "content": "I feel stuck with exams"},
            {"role": "assistant", "content": "Let's start with sleep"},
            {"role": "user", "content": "Also family is stressful"},
        ],
        topic="stress_anxiety",
        safety_mode="normal",
    )

    assert bundle.session_summary.startswith("Topic: stress_anxiety")
    assert "Preferred name: Aykut" in bundle.long_term_memory
    assert "User prefers short answers" in bundle.long_term_memory
    assert "Previously suggested grounding helped" in bundle.long_term_memory
    assert "[Session Memory:" in bundle.prompt_context
    assert "[Profile Memory:" in bundle.prompt_context
    assert len(bundle.recent_turns) == 3
    assert bundle.recent_turns[-1].content == "Also family is stressful"
    assert bundle.debug["recent_segment_count"] == 2
    assert bundle.debug["reflection_count"] == 1


def test_build_memory_bundle_handles_empty_inputs_safely() -> None:
    bundle = build_memory_bundle(session_summary=None, user_memory=None, history=[], topic="general")

    assert bundle.session_summary == ""
    assert bundle.long_term_memory == ""
    assert bundle.prompt_context == ""
    assert bundle.recent_turns == []
    assert bundle.debug["has_session_summary"] is False
    assert bundle.debug["has_user_memory"] is False
