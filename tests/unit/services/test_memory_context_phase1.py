from __future__ import annotations

import pytest

from server.app.services.memory_context import build_memory_bundle, memory_turns_from_history


pytestmark = [pytest.mark.unit]


def test_memory_turns_from_history_keeps_recent_user_and_assistant_turns() -> None:
    turns = memory_turns_from_history(
        [
            {"role": "system", "content": "ignore me"},
            {"role": "user", "content": "I feel lonely"},
            {"role": "assistant", "content": "Tell me more"},
            {"role": "user", "content": "It gets worse at night"},
        ],
        limit=3,
    )

    assert len(turns) == 3
    assert turns[0].role == "user"
    assert turns[-1].content == "It gets worse at night"


def test_build_memory_bundle_includes_recent_turns_in_prompt_context() -> None:
    bundle = build_memory_bundle(
        session_summary="Topic: loneliness.",
        user_memory="Preferred name: Aykut",
        history=[
            {"role": "user", "content": "I feel lonely"},
            {"role": "assistant", "content": "Let's talk about that"},
        ],
        topic="low_mood",
    )

    assert "[Recent Turns:" in bundle.prompt_context
    assert "I feel lonely" in bundle.prompt_context
    assert bundle.debug["recent_turn_count"] == 2
