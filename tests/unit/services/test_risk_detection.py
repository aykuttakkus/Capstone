"""
Unit Tests: RiskDetectionService

Tests the core risk detection logic including:
- Risk level classification
- Risk indicator extraction
- Assessment metadata
- Edge cases
"""

from __future__ import annotations

import pytest
from server.app.services.risk_detection import RiskDetectionService, RiskLevel, RiskAssessment


@pytest.fixture(scope="module")
def detector():
    return RiskDetectionService()


def test_assessment_returns_risk_assessment_object(detector):
    result = detector.assess_response(
        user_message="I'm feeling a bit anxious",
        ai_response="I hear you.",
    )
    assert isinstance(result, RiskAssessment)


def test_risk_assessment_has_required_fields(detector):
    result = detector.assess_response(
        user_message="I want to hurt myself",
        ai_response="I'm here.",
    )
    assert hasattr(result, "risk_level")
    assert hasattr(result, "should_escalate")
    assert hasattr(result, "risk_indicators")
    assert hasattr(result, "escalation_reason")
    assert isinstance(result.risk_indicators, list)


def test_crisis_message_sets_should_escalate_true(detector):
    result = detector.assess_response(
        user_message="I want to kill myself",
        ai_response="I hear you.",
    )
    assert result.should_escalate is True


def test_normal_message_should_escalate_false(detector):
    result = detector.assess_response(
        user_message="I had a pretty good day today",
        ai_response="That's great!",
    )
    assert result.should_escalate is False


def test_risk_indicators_not_empty_for_crisis(detector):
    result = detector.assess_response(
        user_message="I've been thinking about suicide",
        ai_response="I'm here.",
    )
    assert len(result.risk_indicators) > 0


def test_risk_level_ordering():
    assert RiskLevel.NONE < RiskLevel.LOW < RiskLevel.MEDIUM < RiskLevel.HIGH < RiskLevel.CRISIS


def test_medication_message_flagged(detector):
    result = detector.assess_response(
        user_message="I stopped taking my antidepressants without telling my doctor",
        ai_response="It's important to consult your doctor.",
    )
    assert result.risk_level != RiskLevel.NONE


def test_positive_message_is_none_or_low(detector):
    result = detector.assess_response(
        user_message="I'm feeling so much better after talking to you, thank you!",
        ai_response="I'm glad to hear that!",
    )
    assert result.risk_level in (RiskLevel.NONE, RiskLevel.LOW)


def test_cumulative_distress_returns_dict(detector):
    conversation = [
        {"role": "user", "content": "I've been struggling"},
        {"role": "assistant", "content": "I hear you."},
    ]
    result = detector.track_cumulative_distress(conversation)
    assert isinstance(result, dict)
    assert "escalation_needed" in result or "distress_score" in result


def test_empty_conversation_no_escalation(detector):
    result = detector.track_cumulative_distress([])
    assert result.get("escalation_needed") is False or result.get("distress_score", 0) == 0


def test_ai_response_also_scanned(detector):
    """Risk detection must scan AI response, not just user message."""
    result = detector.assess_response(
        user_message="I feel terrible",
        ai_response="If you're thinking about suicide, please call 988 now.",
    )
    assert result.risk_level != RiskLevel.NONE
