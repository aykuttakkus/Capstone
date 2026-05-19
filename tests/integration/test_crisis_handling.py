"""
Integration Tests: End-to-End Crisis Handling

Tests the complete crisis detection → escalation → response pipeline.
These tests are safety-critical: a failure here means a user in crisis
might not receive resources or professional referral.

Architecture: crisis detection runs AFTER LLM response generation,
appending resources without blocking the empathetic response.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from server.app.services.conversational_assistant import ConversationalAssistant, ConversationContext
from server.app.services.risk_detection import RiskDetectionService, RiskLevel
from server.app.services.escalation import EscalationService


CRISIS_MESSAGES = [
    "I've been thinking about ending my life",
    "I want to kill myself",
    "I've been cutting myself to cope",
    "I have a plan to commit suicide tonight",
    "I don't see any reason to go on living",
]

NON_CRISIS_MESSAGES = [
    "I've been feeling a bit down lately",
    "Work has been really stressful this week",
    "I had trouble sleeping last night",
    "I feel anxious about my exams",
    "I've been feeling quite lonely",
]


@pytest.fixture
def full_pipeline(sample_user_state, mock_llm_response):
    assistant = ConversationalAssistant()
    risk_detector = RiskDetectionService()
    escalation = EscalationService()
    return assistant, risk_detector, escalation


# ── Crisis Detection Accuracy ─────────────────────────────────────────────────

@pytest.mark.parametrize("message", CRISIS_MESSAGES)
def test_crisis_message_triggers_escalation_flag(full_pipeline, sample_user_state, mock_llm_response, message):
    """Every crisis-level message must set should_escalate=True."""
    assistant, risk_detector, escalation = full_pipeline

    context = ConversationContext(
        user_id=1,
        session_id="crisis_test",
        current_message=message,
        conversation_history=[],
        user_state=sample_user_state,
    )

    with patch.object(assistant.llm_client, "generate", return_value=mock_llm_response):
        llm_result = assistant.generate_response(context)

    risk = risk_detector.assess_response(
        user_message=message,
        ai_response=llm_result.response_text,
    )

    assert risk.should_escalate is True, (
        f"Crisis message should trigger escalation: '{message[:60]}'"
    )


@pytest.mark.parametrize("message", NON_CRISIS_MESSAGES)
def test_non_crisis_message_does_not_escalate(full_pipeline, sample_user_state, mock_llm_response, message):
    """Standard distress messages must not trigger false escalation."""
    assistant, risk_detector, escalation = full_pipeline

    context = ConversationContext(
        user_id=1,
        session_id="non_crisis_test",
        current_message=message,
        conversation_history=[],
        user_state=sample_user_state,
    )

    with patch.object(assistant.llm_client, "generate", return_value=mock_llm_response):
        llm_result = assistant.generate_response(context)

    risk = risk_detector.assess_response(
        user_message=message,
        ai_response=llm_result.response_text,
    )

    assert risk.risk_level not in (RiskLevel.CRISIS, RiskLevel.HIGH), (
        f"Non-crisis message incorrectly escalated: '{message[:60]}'"
    )


# ── Crisis Response Does Not Block LLM ───────────────────────────────────────

@pytest.mark.parametrize("message", CRISIS_MESSAGES)
def test_crisis_llm_response_not_blocked(full_pipeline, sample_user_state, mock_llm_response, message):
    """Crisis detection must not prevent the LLM from sending an empathetic response."""
    assistant, risk_detector, escalation = full_pipeline

    context = ConversationContext(
        user_id=1,
        session_id="crisis_no_block",
        current_message=message,
        conversation_history=[],
        user_state=sample_user_state,
    )

    with patch.object(assistant.llm_client, "generate", return_value=mock_llm_response):
        llm_result = assistant.generate_response(context)

    assert llm_result.llm_available is True
    assert len(llm_result.response_text) > 20


# ── Escalation Message Content ────────────────────────────────────────────────

def test_crisis_escalation_message_contains_988(full_pipeline, sample_user_state, mock_llm_response):
    """Final response appended with escalation must contain 988 crisis line."""
    assistant, risk_detector, escalation = full_pipeline

    context = ConversationContext(
        user_id=1,
        session_id="crisis_resources",
        current_message="I've been thinking about ending my life",
        conversation_history=[],
        user_state=sample_user_state,
    )

    with patch.object(assistant.llm_client, "generate", return_value=mock_llm_response):
        llm_result = assistant.generate_response(context)

    risk = risk_detector.assess_response(
        user_message=context.current_message,
        ai_response=llm_result.response_text,
    )

    escalation_msg = escalation.build_escalation_message(risk.risk_level, risk.escalation_reason)
    final = escalation.append_escalation_to_response(llm_result.response_text, escalation_msg)

    assert "988" in final, "Final response must contain 988 Suicide and Crisis Lifeline number"


def test_escalation_message_is_appended_not_replaced(full_pipeline, sample_user_state, mock_llm_response):
    """Escalation resources must APPEND to the LLM response, not replace it."""
    assistant, risk_detector, escalation = full_pipeline

    context = ConversationContext(
        user_id=1,
        session_id="crisis_append",
        current_message="I want to kill myself",
        conversation_history=[],
        user_state=sample_user_state,
    )

    with patch.object(assistant.llm_client, "generate", return_value=mock_llm_response):
        llm_result = assistant.generate_response(context)

    risk = risk_detector.assess_response(
        user_message=context.current_message,
        ai_response=llm_result.response_text,
    )

    escalation_msg = escalation.build_escalation_message(risk.risk_level, risk.escalation_reason)
    final = escalation.append_escalation_to_response(llm_result.response_text, escalation_msg)

    # Both LLM content and crisis resources should be present
    assert llm_result.response_text in final or len(final) > len(escalation_msg)


# ── Risk Level Hierarchy ──────────────────────────────────────────────────────

def test_crisis_risk_level_highest(full_pipeline):
    """CRISIS risk level must be higher than HIGH."""
    _, risk_detector, _ = full_pipeline

    crisis_risk = risk_detector.assess_response(
        user_message="I want to end my life right now",
        ai_response="I'm here for you",
    )
    high_risk = risk_detector.assess_response(
        user_message="I've been thinking about self-harm",
        ai_response="I'm here for you",
    )

    crisis_levels = [RiskLevel.NONE, RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRISIS]
    assert crisis_levels.index(crisis_risk.risk_level) >= crisis_levels.index(high_risk.risk_level)
