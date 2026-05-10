from __future__ import annotations

import pytest

from server.app.core.generation.generator import AnswerGenerator
from server.app.core.safety.policy import SafetyDecision
from tests.factories.retrieval import build_scored_chunk


pytestmark = [pytest.mark.unit]


def test_grounded_generation_uses_mock_backend_when_available(mock_llm_backend) -> None:
    generator = AnswerGenerator(llm_client=mock_llm_backend)
    payload = generator.build_grounded(
        message="Tell me about stress and sleep",
        topic="burnout_sleep",
        retrievals=[build_scored_chunk("sleep-001", topic="burnout_sleep", score=0.95)],
        intent_label="psychoeducation",
    )

    assert payload.status == "grounded"
    assert payload.answer == "Grounded answer from mock backend."
    assert payload.route == "topic:burnout_sleep"


def test_grounded_generation_falls_back_to_source_summary_when_llm_is_offline(offline_llm_backend) -> None:
    generator = AnswerGenerator(llm_client=offline_llm_backend)
    payload = generator.build_grounded(
        message="Tell me about stress and sleep",
        topic="burnout_sleep",
        retrievals=[build_scored_chunk("sleep-001", topic="burnout_sleep", score=0.95)],
        intent_label="psychoeducation",
    )

    assert payload.status == "insufficient_evidence"
    assert "I do not have enough reliable evidence" in payload.answer


def test_insufficient_and_special_generation_paths_are_explicit() -> None:
    generator = AnswerGenerator()
    insufficient = generator.build_insufficient("low_mood", "psychoeducation")
    general_fallback = generator.build_insufficient("general", "psychoeducation")
    special = generator.build_special(
        SafetyDecision(
            mode="diagnosis_refusal",
            reason="diagnosis_request_detected",
            message="I cannot diagnose conditions.",
            risk_level=0,
        ),
        topic="low_mood",
        intent_label="psychoeducation",
    )
    clarification = generator.build_special(
        SafetyDecision(
            mode="risk_clarification",
            reason="ambiguous_distress_detected",
            message="I want to check in before we continue.",
            risk_level=1,
        ),
        topic="low_mood",
        intent_label="psychoeducation",
    )

    assert insufficient.status == "insufficient_evidence"
    assert insufficient.route == "evidence_gate"
    assert general_fallback.status == "general_fallback"
    assert general_fallback.route == "topic:general"
    assert "general psychoeducational overview" in general_fallback.answer
    assert clarification.status == "clarification"
    assert clarification.route == "risk_clarification"
    assert "reply with 'safe'" in clarification.answer
    assert special.status == "refusal"
    assert special.route == "diagnosis_refusal"
