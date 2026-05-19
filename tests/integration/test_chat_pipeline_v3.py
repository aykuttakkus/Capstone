"""
Integration Tests: Full v3 Chat Pipeline

End-to-end tests that validate the complete conversational flow:
User Message → User State → RAG → LLM → Risk Detection → Response

These tests use mocked LLM but real service logic.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from server.app.services.conversational_assistant import ConversationalAssistant, ConversationContext
from server.app.services.risk_detection import RiskDetectionService, RiskLevel
from server.app.services.escalation import EscalationService


@pytest.fixture
def pipeline_components(sample_user_state, mock_llm_response):
    """Complete v3 pipeline with mocked LLM."""
    assistant = ConversationalAssistant()
    risk_detector = RiskDetectionService()
    escalation = EscalationService()
    return assistant, risk_detector, escalation


# ── Normal Conversation Flow ──────────────────────────────────────────────────

def test_non_crisis_message_no_escalation(pipeline_components, sample_user_state, mock_llm_response):
    assistant, risk_detector, escalation = pipeline_components

    context = ConversationContext(
        user_id="1",
        session_id="session_001",
        current_message="I've been feeling a bit lonely lately",
        conversation_history=[],
        user_state=sample_user_state,
        retrieved_knowledge="Loneliness is associated with decreased wellbeing.",
    )

    with patch.object(assistant.llm_client, "generate", return_value=mock_llm_response):
        llm_result = assistant.generate_response(context)

    risk = risk_detector.assess_response(
        user_message=context.current_message,
        ai_response=llm_result.response_text,
    )

    assert llm_result.llm_available is True
    assert len(llm_result.response_text) > 20
    assert risk.risk_level in (RiskLevel.NONE, RiskLevel.LOW, RiskLevel.MEDIUM)


def test_multi_turn_context_preserved(pipeline_components, sample_user_state, mock_llm_response):
    assistant, _, _ = pipeline_components

    history = [
        {"role": "user", "content": "I've been struggling with anxiety"},
        {"role": "assistant", "content": "I hear you. Anxiety can be really challenging."},
        {"role": "user", "content": "Like I mentioned, it's been going on for weeks"},
    ]

    context = ConversationContext(
        user_id="1",
        session_id="session_002",
        current_message="Can you suggest some techniques?",
        conversation_history=history,
        user_state=sample_user_state,
    )

    with patch.object(assistant.llm_client, "generate", return_value=mock_llm_response):
        result = assistant.generate_response(context)

    assert "history" in result.context_used


# ── Crisis Flow ───────────────────────────────────────────────────────────────

def test_crisis_message_triggers_escalation(pipeline_components, sample_user_state, mock_llm_response):
    assistant, risk_detector, escalation = pipeline_components

    context = ConversationContext(
        user_id="1",
        session_id="session_crisis",
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

    assert risk.should_escalate is True
    assert risk.risk_level in (RiskLevel.CRISIS, RiskLevel.HIGH)


def test_crisis_response_contains_resources(pipeline_components, sample_user_state, mock_llm_response):
    """AI response + escalation message must contain crisis resources."""
    assistant, risk_detector, escalation = pipeline_components

    context = ConversationContext(
        user_id="1",
        session_id="session_crisis_2",
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
    final_response = escalation.append_escalation_to_response(
        llm_result.response_text, escalation_msg
    )

    assert "988" in final_response, "Final response must contain 988 crisis line"


def test_crisis_response_not_blocked(pipeline_components, sample_user_state, mock_llm_response):
    """Crisis detection must NOT block the AI response — it appends resources."""
    assistant, risk_detector, escalation = pipeline_components

    context = ConversationContext(
        user_id="1",
        session_id="session_crisis_3",
        current_message="I've been thinking about suicide",
        conversation_history=[],
        user_state=sample_user_state,
    )

    with patch.object(assistant.llm_client, "generate", return_value=mock_llm_response):
        llm_result = assistant.generate_response(context)

    # The original empathetic response must be present
    assert len(llm_result.response_text) > 20
    assert llm_result.llm_available is True


# ── User State Integration ────────────────────────────────────────────────────

def test_user_state_reflected_in_context_used(pipeline_components, sample_user_state, mock_llm_response):
    assistant, _, _ = pipeline_components

    context = ConversationContext(
        user_id="1",
        session_id="session_state",
        current_message="I feel anxious",
        conversation_history=[],
        user_state=sample_user_state,
    )

    with patch.object(assistant.llm_client, "generate", return_value=mock_llm_response):
        result = assistant.generate_response(context)

    assert "profile" in result.context_used
    assert "mood" in result.context_used


def test_no_user_state_still_works(pipeline_components, mock_llm_response):
    assistant, _, _ = pipeline_components

    context = ConversationContext(
        user_id="1",
        session_id="session_no_state",
        current_message="I need some help",
        conversation_history=[],
        user_state=None,
    )

    with patch.object(assistant.llm_client, "generate", return_value=mock_llm_response):
        result = assistant.generate_response(context)

    assert result.llm_available is True
    assert len(result.response_text) > 0
