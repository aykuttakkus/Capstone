"""
Unit Tests: ContextFormatter

Tests the service that converts structured user state into natural language
narratives suitable for injection into the LLM system prompt.

Key requirement: context must feel like the LLM's natural background knowledge,
not a JSON dump — verified by checking the output reads as prose.
"""

from __future__ import annotations

import pytest
from server.app.services.context_formatter import ContextFormatter
from server.app.services.user_state import UserState


def make_state(**overrides) -> UserState:
    defaults = dict(
        user_id=1,
        preferred_name=None,
        primary_concerns=None,
        goals_for_support=None,
        communication_style=None,
        response_length_preference=None,
        coping_strategies_helpful=None,
        coping_strategies_unhelpful=None,
        main_triggers=None,
        support_system=None,
        life_narrative=None,
        therapy_status=None,
        mood_summary=None,
        recent_mood_score=None,
        recent_anxiety_score=None,
        mood_pattern_tags=[],
        journal_summary=None,
        journal_themes=[],
        personalization_consent=True,
        use_mood_context=True,
        use_journal_context=True,
        use_memory_context=False,
    )
    defaults.update(overrides)
    return UserState(**defaults)


# ── Basic Output ──────────────────────────────────────────────────────────────

def test_format_returns_string_or_empty(sample_user_state):
    result = ContextFormatter.format_full_context(user_state=sample_user_state)
    assert isinstance(result, str)


def test_format_with_no_inputs_returns_empty():
    result = ContextFormatter.format_full_context()
    assert result == "" or result is None


def test_format_with_none_user_state():
    result = ContextFormatter.format_full_context(user_state=None, conversation_history=[])
    assert result == "" or result is None


# ── Profile Narrative ─────────────────────────────────────────────────────────

def test_preferred_name_appears_in_output():
    state = make_state(preferred_name="Riley")
    result = ContextFormatter.format_full_context(user_state=state)
    assert "Riley" in result


def test_primary_concerns_appear_in_output():
    state = make_state(primary_concerns="social anxiety and isolation")
    result = ContextFormatter.format_full_context(user_state=state)
    assert "anxiety" in result.lower() or "isolation" in result.lower()


def test_therapy_status_yes_mention():
    state = make_state(therapy_status="yes, weekly sessions")
    result = ContextFormatter.format_full_context(user_state=state)
    assert "therapist" in result.lower() or "professional" in result.lower()


def test_therapy_status_no_mention():
    state = make_state(therapy_status="no")
    result = ContextFormatter.format_full_context(user_state=state)
    assert result is not None  # at minimum should not crash


def test_coping_strategies_helpful_in_output():
    state = make_state(
        coping_strategies_helpful="deep breathing",
        support_system="close friends",
    )
    result = ContextFormatter.format_full_context(user_state=state)
    assert "breathing" in result.lower() or "friends" in result.lower()


def test_life_narrative_truncated_to_200():
    long_narrative = "A" * 500
    state = make_state(life_narrative=long_narrative)
    result = ContextFormatter.format_full_context(user_state=state)
    # Should appear but truncated
    assert "A" * 200 in result
    assert "A" * 300 not in result


# ── Mood / Wellness Narrative ─────────────────────────────────────────────────

def test_mood_summary_in_output():
    state = make_state(mood_summary="consistently low mood over two weeks")
    result = ContextFormatter.format_full_context(user_state=state)
    assert "low mood" in result.lower()


def test_low_mood_score_described():
    state = make_state(recent_mood_score=2.0)
    result = ContextFormatter.format_full_context(user_state=state)
    assert "low" in result.lower()


def test_elevated_anxiety_score_described():
    state = make_state(recent_anxiety_score=8.5)
    result = ContextFormatter.format_full_context(user_state=state)
    assert "anxiety" in result.lower()


def test_journal_summary_in_output():
    state = make_state(journal_summary="Wrote about exam stress and fear of failure")
    result = ContextFormatter.format_full_context(user_state=state)
    assert "exam" in result.lower() or "stress" in result.lower()


# ── Intake Narrative ──────────────────────────────────────────────────────────

def test_intake_data_included_when_provided():
    intake = {
        "main_issue": "persistent anxiety",
        "timeline": "six months",
        "help_type": "coping tools",
    }
    result = ContextFormatter.format_full_context(intake_data=intake)
    assert "anxiety" in result.lower()
    assert "six months" in result.lower() or "months" in result.lower()


def test_intake_empty_dict_does_not_crash():
    result = ContextFormatter.format_full_context(intake_data={})
    assert isinstance(result, str)


# ── Conversation Trajectory ───────────────────────────────────────────────────

def test_short_history_below_threshold_no_trajectory():
    """Fewer than 4 turns → no trajectory narrative added."""
    history = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello, how can I help?"},
    ]
    result = ContextFormatter.format_full_context(conversation_history=history)
    # Should return empty or minimal output (no trajectory)
    assert result == "" or "opening up" not in result


def test_distress_heavy_history_flagged():
    history = [
        {"role": "user", "content": "I'm really struggling and overwhelmed"},
        {"role": "assistant", "content": "I hear you, that sounds very hard."},
        {"role": "user", "content": "I'm so tired and anxious all the time"},
        {"role": "assistant", "content": "Let's work through this together."},
    ]
    result = ContextFormatter.format_full_context(conversation_history=history)
    assert "struggle" in result.lower() or "overwhelm" in result.lower()


def test_sleep_topic_detected_in_trajectory():
    history = [
        {"role": "user", "content": "I can't sleep"},
        {"role": "assistant", "content": "Tell me more."},
        {"role": "user", "content": "I'm totally exhausted every day"},
        {"role": "assistant", "content": "Sleep difficulties are really draining."},
    ]
    result = ContextFormatter.format_full_context(conversation_history=history)
    assert "sleep" in result.lower() or "fatigue" in result.lower()
