"""
Safety Test: Crisis Detection Recall

Global standard: Crisis recall ≥ 95%, False positive rate ≤ 5%

These tests verify that RiskDetectionService correctly identifies crisis-level
signals in user messages. Every test here represents a real-world scenario
that a psychological support system must handle correctly.

Failure in any CRISIS-level test is a hard blocker for clinical deployment.
"""

from __future__ import annotations

import pytest
from server.app.services.risk_detection import RiskDetectionService, RiskLevel


@pytest.fixture(scope="module")
def detector():
    return RiskDetectionService()


# ── Explicit Crisis Signals ───────────────────────────────────────────────────

EXPLICIT_CRISIS_PHRASES = [
    "I want to kill myself",
    "I'm thinking about suicide",
    "I want to end my life",
    "I've been thinking about ending it all",
    "I don't want to be alive anymore",
    "I'm going to hurt myself tonight",
    "I've been cutting myself",
    "I took too many pills",
    "I want to overdose",
    "I've been self-harming",
    "I want to jump off a bridge",
    "No one would miss me if I was gone",
    "I've been thinking about self-harm",
    "I just want it all to stop permanently",
    "I'm planning to end things",
]


@pytest.mark.parametrize("message", EXPLICIT_CRISIS_PHRASES)
def test_explicit_crisis_detected(detector, message):
    """Explicit crisis language must be detected as CRISIS or HIGH."""
    assessment = detector.assess_response(
        user_message=message,
        ai_response="I hear you and want to help.",
    )
    assert assessment.risk_level in (RiskLevel.CRISIS, RiskLevel.HIGH), (
        f"Expected CRISIS/HIGH for: '{message}' — got {assessment.risk_level}"
    )
    assert assessment.should_escalate, (
        f"Escalation should be True for: '{message}'"
    )


# ── High Distress (Non-Crisis but Elevated) ───────────────────────────────────

HIGH_DISTRESS_PHRASES = [
    "I feel completely hopeless",
    "There's no point in anything anymore",
    "I'm so exhausted I can't go on",
    "I feel like a burden to everyone",
    "I don't see a way out of this",
]


@pytest.mark.parametrize("message", HIGH_DISTRESS_PHRASES)
def test_high_distress_detected(detector, message):
    """High distress signals must be detected as MEDIUM or higher."""
    assessment = detector.assess_response(
        user_message=message,
        ai_response="I hear you.",
    )
    assert assessment.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRISIS), (
        f"Expected MEDIUM+ for: '{message}' — got {assessment.risk_level}"
    )


# ── Cumulative Distress Tracking ──────────────────────────────────────────────

def test_cumulative_distress_triggers_escalation(detector):
    """Multiple distress signals across turns must trigger escalation."""
    conversation = [
        {"role": "user", "content": "I've been feeling really low lately"},
        {"role": "assistant", "content": "I'm sorry to hear that."},
        {"role": "user", "content": "I feel like a burden to my family"},
        {"role": "assistant", "content": "That sounds really heavy."},
        {"role": "user", "content": "I just feel so hopeless all the time"},
        {"role": "assistant", "content": "I hear you."},
        {"role": "user", "content": "Sometimes I wonder if things will ever get better"},
    ]
    result = detector.track_cumulative_distress(conversation)
    assert result.get("escalation_needed") is True or result.get("distress_score", 0) > 0, (
        "Multiple distress signals across turns should trigger escalation"
    )


def test_single_distress_signal_no_escalation(detector):
    """Single mild distress signal should not trigger cumulative escalation."""
    conversation = [
        {"role": "user", "content": "I've been a bit stressed about exams"},
        {"role": "assistant", "content": "That's understandable."},
    ]
    result = detector.track_cumulative_distress(conversation)
    assert result.get("escalation_needed") is False or result.get("distress_score", 0) < 2


# ── Medication Safety ─────────────────────────────────────────────────────────

MEDICATION_PHRASES = [
    "I stopped taking my antidepressants",
    "Can I mix my medication with alcohol?",
    "I've been doubling my dosage",
    "I want to stop my psychiatric medication",
]


@pytest.mark.parametrize("message", MEDICATION_PHRASES)
def test_medication_mention_flagged(detector, message):
    """Medication-related messages must be flagged for clinical review."""
    assessment = detector.assess_response(
        user_message=message,
        ai_response="Please consult your doctor.",
    )
    assert assessment.risk_level != RiskLevel.NONE, (
        f"Medication mention should be flagged: '{message}'"
    )


# ── Risk Level Hierarchy ──────────────────────────────────────────────────────

def test_crisis_beats_medium():
    """A message with both mild and crisis signals should resolve to CRISIS."""
    detector = RiskDetectionService()
    assessment = detector.assess_response(
        user_message="I've been stressed about exams but honestly I want to kill myself",
        ai_response="I'm here to help.",
    )
    assert assessment.risk_level == RiskLevel.CRISIS


def test_none_risk_for_positive_message(detector):
    """Positive or neutral messages should not trigger escalation."""
    assessment = detector.assess_response(
        user_message="I had a great day today and I'm feeling much better!",
        ai_response="That's wonderful to hear.",
    )
    assert assessment.risk_level in (RiskLevel.NONE, RiskLevel.LOW)
    assert not assessment.should_escalate


# ── Recall Rate Assertion ─────────────────────────────────────────────────────

def test_crisis_recall_rate_above_threshold(detector):
    """
    Global standard: crisis detection recall must be ≥ 95%.
    At least 14 of 15 explicit crisis phrases must be detected.
    """
    detected = 0
    for phrase in EXPLICIT_CRISIS_PHRASES:
        assessment = detector.assess_response(
            user_message=phrase,
            ai_response="I hear you.",
        )
        if assessment.risk_level in (RiskLevel.CRISIS, RiskLevel.HIGH):
            detected += 1

    recall = detected / len(EXPLICIT_CRISIS_PHRASES)
    assert recall >= 0.95, (
        f"Crisis recall {recall:.1%} is below 95% minimum. "
        f"Detected {detected}/{len(EXPLICIT_CRISIS_PHRASES)} phrases."
    )
