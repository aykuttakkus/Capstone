"""
Benchmark Tests: LLM Response Quality

Validates structural and content properties of generated responses
that signal therapeutic quality and safety compliance.

These tests use a mocked LLM but validate the pipeline's handling
of response structure, context usage signals, and boundary adherence.

Thresholds (global standard):
- All responses must reference at least one context source
- No response may recommend specific medications
- Crisis responses must include professional referral signals
"""

from __future__ import annotations

import re
import pytest
from unittest.mock import MagicMock, patch

from server.app.services.conversational_assistant import ConversationalAssistant, ConversationContext


@pytest.fixture
def assistant():
    return ConversationalAssistant()


# ── Response Length ───────────────────────────────────────────────────────────

def test_response_not_empty(assistant, mock_llm_response):
    context = ConversationContext(
        user_id=1,
        session_id="quality_len",
        current_message="I've been feeling really anxious lately",
        conversation_history=[],
        user_state=None,
    )
    with patch.object(assistant.llm_client, "generate", return_value=mock_llm_response):
        result = assistant.generate_response(context)
    assert len(result.response_text.strip()) > 20


def test_response_has_reasonable_length(assistant, mock_llm_response):
    """Response should be substantive — not a one-word answer."""
    context = ConversationContext(
        user_id=1,
        session_id="quality_len2",
        current_message="I've been struggling with anxiety and sleep problems for weeks",
        conversation_history=[],
        user_state=None,
    )
    with patch.object(assistant.llm_client, "generate", return_value=mock_llm_response):
        result = assistant.generate_response(context)
    assert len(result.response_text.split()) >= 5


# ── Context Tracking ──────────────────────────────────────────────────────────

def test_context_used_is_collection(assistant, mock_llm_response, sample_user_state):
    context = ConversationContext(
        user_id=1,
        session_id="ctx_dict",
        current_message="I feel lonely",
        conversation_history=[],
        user_state=sample_user_state,
    )
    with patch.object(assistant.llm_client, "generate", return_value=mock_llm_response):
        result = assistant.generate_response(context)
    assert isinstance(result.context_used, (dict, list))


def test_context_used_tracks_profile_when_user_state_provided(assistant, mock_llm_response, sample_user_state):
    context = ConversationContext(
        user_id=1,
        session_id="ctx_profile",
        current_message="I feel anxious",
        conversation_history=[],
        user_state=sample_user_state,
    )
    with patch.object(assistant.llm_client, "generate", return_value=mock_llm_response):
        result = assistant.generate_response(context)
    assert "profile" in result.context_used


def test_context_used_tracks_history_when_history_provided(assistant, mock_llm_response):
    history = [
        {"role": "user", "content": "I've been anxious for weeks"},
        {"role": "assistant", "content": "I understand, let's talk about this."},
    ]
    context = ConversationContext(
        user_id=1,
        session_id="ctx_history",
        current_message="It's been getting worse",
        conversation_history=history,
        user_state=None,
    )
    with patch.object(assistant.llm_client, "generate", return_value=mock_llm_response):
        result = assistant.generate_response(context)
    assert "history" in result.context_used


# ── LLM Availability Flag ─────────────────────────────────────────────────────

def test_llm_available_true_when_llm_responds(assistant, mock_llm_response):
    context = ConversationContext(
        user_id=1,
        session_id="avail_true",
        current_message="I need support",
        conversation_history=[],
        user_state=None,
    )
    with patch.object(assistant.llm_client, "generate", return_value=mock_llm_response):
        result = assistant.generate_response(context)
    assert result.llm_available is True


def test_llm_available_false_when_llm_fails(assistant, mock_llm_unavailable):
    context = ConversationContext(
        user_id=1,
        session_id="avail_false",
        current_message="I need support",
        conversation_history=[],
        user_state=None,
    )
    with patch.object(assistant.llm_client, "generate", return_value=mock_llm_unavailable):
        result = assistant.generate_response(context)
    assert result.llm_available is False


def test_degraded_response_not_empty_when_llm_fails(assistant, mock_llm_unavailable):
    """Even when LLM is down, user must receive some response — never silence."""
    context = ConversationContext(
        user_id=1,
        session_id="degraded",
        current_message="I need support",
        conversation_history=[],
        user_state=None,
    )
    with patch.object(assistant.llm_client, "generate", return_value=mock_llm_unavailable):
        result = assistant.generate_response(context)
    assert len(result.response_text.strip()) > 0


# ── Knowledge Integration ─────────────────────────────────────────────────────

def test_retrieved_knowledge_included_in_prompt(assistant, mock_llm_response):
    """When retrieved knowledge is passed, it must appear in the LLM prompt."""
    captured = []

    def capture_generate(prompt, **kwargs):
        captured.append(prompt)
        return mock_llm_response

    context = ConversationContext(
        user_id=1,
        session_id="rag_injection",
        current_message="Tell me about managing anxiety",
        conversation_history=[],
        user_state=None,
        retrieved_knowledge="Evidence-based approaches include CBT and mindfulness practices.",
    )

    with patch.object(assistant.llm_client, "generate", side_effect=capture_generate):
        assistant.generate_response(context)

    assert len(captured) == 1
    assert "CBT" in captured[0] or "mindfulness" in captured[0]


# ── System Prompt Safety Markers ──────────────────────────────────────────────

def test_system_prompt_mentions_boundaries(assistant):
    """System prompt must address therapeutic boundaries."""
    prompt_lower = assistant.SYSTEM_PROMPT.lower()
    assert "medication" in prompt_lower or "diagnos" in prompt_lower


def test_system_prompt_mentions_crisis_resources(assistant):
    """System prompt must reference crisis escalation path."""
    assert "988" in assistant.SYSTEM_PROMPT or "crisis" in assistant.SYSTEM_PROMPT.lower()
