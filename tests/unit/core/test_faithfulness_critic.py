from __future__ import annotations

from server.app.core.agents.faithfulness_critic import FaithfulnessCritic
from server.app.core.agents.response_planner import ResponsePlan
from tests.factories.retrieval import build_scored_chunk


def _plan(**overrides) -> ResponsePlan:
    values = {
        "intent": "psychoeducation",
        "topic": "stress_anxiety",
        "risk_mode": "normal",
        "knowledge_need": True,
        "memory_need": False,
        "tone_plan": "warm",
        "support_goal": "grounded_psychoeducation",
        "recommended_structure": "direct_answer",
        "source_mode": "grounded",
        "primary_intent": "psychoeducation",
        "needs_rag": True,
        "response_mode": "education",
        "source_required": True,
    }
    values.update(overrides)
    return ResponsePlan(**values)


def test_faithfulness_critic_blocks_diagnostic_claim() -> None:
    critic = FaithfulnessCritic()

    result = critic.critique(
        "You have depression.",
        [build_scored_chunk("a")],
        _plan(),
        retrieval_confidence=0.9,
    )

    assert result.passed is False
    assert result.rewrite_required is True
    assert result.unsupported_claims


def test_faithfulness_critic_blocks_source_required_without_retrieval() -> None:
    critic = FaithfulnessCritic()

    result = critic.critique(
        "Research proves this always works.",
        [],
        _plan(),
        retrieval_confidence=0.0,
    )

    assert result.passed is False
    assert "source_required_but_no_retrieval" in result.unsupported_claims


def test_faithfulness_critic_blocks_crisis_source_in_normal_response() -> None:
    critic = FaithfulnessCritic()

    result = critic.critique(
        "Here is general education.",
        [
            build_scored_chunk(
                "crisis",
                clinical_scope="crisis_support_only",
                allowed_use=["crisis"],
                risk_level="crisis",
            )
        ],
        _plan(response_mode="education"),
        retrieval_confidence=0.9,
    )

    assert result.passed is False
    assert result.source_misuse
