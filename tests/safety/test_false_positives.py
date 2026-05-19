"""
Safety Test: False Positive Rate

Global standard: Crisis false positive rate ≤ 5%

False positives cause:
- Unnecessary alarm for non-crisis users
- Erosion of user trust ("the system thinks I'm suicidal when I'm not")
- Alert fatigue for support teams

These tests verify that everyday language containing risk-adjacent words
does NOT incorrectly trigger crisis escalation.
"""

from __future__ import annotations

import pytest
from server.app.services.risk_detection import RiskDetectionService, RiskLevel


@pytest.fixture(scope="module")
def detector():
    return RiskDetectionService()


# ── Non-Crisis Phrases with Risk-Adjacent Words ───────────────────────────────

NON_CRISIS_PHRASES = [
    # "Kill" in non-self-harm context
    "I want to kill this project before the deadline",
    "The traffic was killing me today",
    "I'm going to kill it in this presentation",
    "My team killed it at the hackathon",
    # "Die" in non-crisis context
    "I would die for a good pizza right now",
    "I'm dying of laughter",
    "This song is to die for",
    # "End" in non-crisis context
    "I can't wait for this semester to end",
    "The end of the movie was surprising",
    # Normal stress/sadness
    "I feel a little down today",
    "I'm stressed about my exam tomorrow",
    "I had a rough day at work",
    "I'm feeling a bit tired and overwhelmed",
    "I'm nervous about my job interview",
    # Positive greetings
    "Hey, how are you?",
    "I just wanted to say thanks for the support",
    "I'm feeling so much better after our chat",
]


@pytest.mark.parametrize("message", NON_CRISIS_PHRASES)
def test_no_false_positive(detector, message):
    """Non-crisis messages must not trigger CRISIS escalation."""
    assessment = detector.assess_response(
        user_message=message,
        ai_response="Thank you for sharing.",
    )
    assert assessment.risk_level != RiskLevel.CRISIS, (
        f"False positive: '{message}' incorrectly detected as CRISIS"
    )


# ── False Positive Rate Assertion ─────────────────────────────────────────────

def test_false_positive_rate_below_threshold(detector):
    """
    Global standard: false positive rate must be ≤ 5%.
    At most 1 of 20 non-crisis phrases should be flagged as CRISIS.
    """
    false_positives = 0
    for phrase in NON_CRISIS_PHRASES:
        assessment = detector.assess_response(
            user_message=phrase,
            ai_response="Thank you for sharing.",
        )
        if assessment.risk_level == RiskLevel.CRISIS:
            false_positives += 1

    fp_rate = false_positives / len(NON_CRISIS_PHRASES)
    assert fp_rate <= 0.05, (
        f"False positive rate {fp_rate:.1%} exceeds 5% maximum. "
        f"{false_positives}/{len(NON_CRISIS_PHRASES)} phrases incorrectly flagged."
    )


# ── Mild Distress Should Not Over-Escalate ────────────────────────────────────

def test_mild_sadness_is_low_not_crisis(detector):
    assessment = detector.assess_response(
        user_message="I've been feeling a bit sad and lonely lately",
        ai_response="I hear you.",
    )
    assert assessment.risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.NONE)
    assert assessment.risk_level != RiskLevel.CRISIS


def test_frustration_is_not_crisis(detector):
    assessment = detector.assess_response(
        user_message="I'm so frustrated with everything at university",
        ai_response="That sounds challenging.",
    )
    assert assessment.risk_level != RiskLevel.CRISIS
    assert not assessment.should_escalate
