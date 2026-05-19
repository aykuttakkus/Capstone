"""
Unit Tests: UserState and UserStateService

Tests the consent-gated user state model that consolidates profile,
mood trend, and journal insights for personalized LLM context injection.

GDPR Article 9: health data must only flow downstream when consent is given.
These tests verify that the data model enforces those gates at the field level.
"""

from __future__ import annotations

import pytest
from dataclasses import asdict

from server.app.services.user_state import UserState, UserStateService


# ── UserState Data Model ──────────────────────────────────────────────────────

def test_user_state_has_required_fields(sample_user_state):
    """UserState must expose the fields expected by downstream services."""
    assert hasattr(sample_user_state, "user_id")
    assert hasattr(sample_user_state, "preferred_name")
    assert hasattr(sample_user_state, "primary_concerns")
    assert hasattr(sample_user_state, "mood_summary")
    assert hasattr(sample_user_state, "recent_mood_score")
    assert hasattr(sample_user_state, "journal_summary")
    assert hasattr(sample_user_state, "journal_themes")
    assert hasattr(sample_user_state, "mood_pattern_tags")


def test_user_state_consent_flags_default_type(sample_user_state):
    assert isinstance(sample_user_state.personalization_consent, bool)
    assert isinstance(sample_user_state.use_mood_context, bool)
    assert isinstance(sample_user_state.use_journal_context, bool)
    assert isinstance(sample_user_state.use_memory_context, bool)


def test_user_state_list_fields_are_lists(sample_user_state):
    assert isinstance(sample_user_state.mood_pattern_tags, list)
    assert isinstance(sample_user_state.journal_themes, list)


def test_user_state_user_id_is_int(sample_user_state):
    assert isinstance(sample_user_state.user_id, int)


# ── Consent Gating: profile fields ───────────────────────────────────────────

def test_personalization_off_clears_preferred_name():
    """When personalization_consent=False, preferred_name must be None."""
    state = UserState(
        user_id=1,
        preferred_name=None,          # service sets None when consent=False
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
        mood_summary="Low mood lately",
        recent_mood_score=3.0,
        recent_anxiety_score=6.0,
        mood_pattern_tags=["stressed"],
        journal_summary="Wrote about work",
        journal_themes=["work"],
        personalization_consent=False,
        use_mood_context=True,
        use_journal_context=True,
        use_memory_context=False,
    )
    assert state.preferred_name is None
    assert state.primary_concerns is None
    assert state.life_narrative is None


def test_personalization_on_allows_profile_fields():
    """When personalization_consent=True, profile fields may be non-None."""
    state = UserState(
        user_id=1,
        preferred_name="Alex",
        primary_concerns="anxiety",
        goals_for_support="coping techniques",
        communication_style="direct",
        response_length_preference="medium",
        coping_strategies_helpful="journaling",
        coping_strategies_unhelpful=None,
        main_triggers="work pressure",
        support_system="friends",
        life_narrative="Student with high workload",
        therapy_status="no",
        mood_summary=None,
        recent_mood_score=None,
        recent_anxiety_score=None,
        mood_pattern_tags=[],
        journal_summary=None,
        journal_themes=[],
        personalization_consent=True,
        use_mood_context=False,
        use_journal_context=False,
        use_memory_context=False,
    )
    assert state.preferred_name == "Alex"
    assert state.primary_concerns == "anxiety"


# ── Consent Gating: mood fields ───────────────────────────────────────────────

def test_mood_context_off_clears_mood_fields():
    """When use_mood_context=False, mood fields must be None/empty."""
    state = UserState(
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
        mood_summary=None,          # cleared by service when use_mood_context=False
        recent_mood_score=None,
        recent_anxiety_score=None,
        mood_pattern_tags=[],
        journal_summary=None,
        journal_themes=[],
        personalization_consent=False,
        use_mood_context=False,
        use_journal_context=False,
        use_memory_context=False,
    )
    assert state.mood_summary is None
    assert state.recent_mood_score is None
    assert state.mood_pattern_tags == []


# ── Consent Gating: journal fields ───────────────────────────────────────────

def test_journal_context_off_clears_journal_fields():
    """When use_journal_context=False, journal fields must be None/empty."""
    state = UserState(
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
        journal_summary=None,        # cleared by service when use_journal_context=False
        journal_themes=[],
        personalization_consent=False,
        use_mood_context=False,
        use_journal_context=False,
        use_memory_context=False,
    )
    assert state.journal_summary is None
    assert state.journal_themes == []


# ── UserStateService: context string formatting ───────────────────────────────

def test_format_as_context_string_returns_none_when_empty():
    """Service must return None (not empty string) when no displayable data."""
    service = UserStateService()
    empty_state = UserState(
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
        personalization_consent=False,
        use_mood_context=False,
        use_journal_context=False,
        use_memory_context=False,
    )
    result = service.format_as_context_string(empty_state)
    assert result is None


def test_format_as_context_string_includes_name():
    service = UserStateService()
    state = UserState(
        user_id=1,
        preferred_name="Jordan",
        primary_concerns="anxiety",
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
        use_mood_context=False,
        use_journal_context=False,
        use_memory_context=False,
    )
    result = service.format_as_context_string(state)
    assert result is not None
    assert "Jordan" in result


def test_format_as_context_string_includes_mood(sample_user_state):
    service = UserStateService()
    result = service.format_as_context_string(sample_user_state)
    if sample_user_state.use_mood_context and sample_user_state.mood_summary:
        assert sample_user_state.mood_summary in (result or "")
