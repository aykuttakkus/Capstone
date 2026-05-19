from __future__ import annotations

import json

import pytest

from server.app.services.session import (
    build_session_summary,
    compact_memory_text,
    compose_memory_context,
    prune_memory_text,
)


pytestmark = [pytest.mark.unit]


def test_compose_memory_context_joins_session_and_long_term_memory() -> None:
    context = compose_memory_context("Session summary", "Long-term memory")
    assert "[Session Memory: Session summary]" in context
    assert "[Long-term Memory: Long-term memory]" in context


def test_compact_and_prune_memory_keep_output_bounded() -> None:
    text = "Line one\n\nLine two\n\nLine three\n\nLine four\n\nLine five\n\nLine six\n\nLine seven"
    compacted = compact_memory_text(text, max_chars=30)
    pruned = prune_memory_text(text, max_lines=3, max_chars=120)
    assert compacted.endswith("...")
    assert len(pruned) <= 120
    assert pruned.startswith("Line one")


def test_build_session_summary_includes_core_context() -> None:
    summary = build_session_summary(
        {"main_issue": "Stress", "help_type": "Sources"},
        "This answer explains stress and sleep.",
        topic="stress_anxiety",
        intent="psychoeducation",
        safety_mode="normal",
    )
    parsed = json.loads(summary.recap)

    assert parsed["main_concern"] == "Stress"
    assert parsed["user_goal"] == "Sources"
    assert parsed["last_response_mode"] == "psychoeducation"
    assert parsed["important_new_information"] == ["Topic: stress_anxiety", "Safety mode: normal"]
