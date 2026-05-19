from __future__ import annotations

import pytest

from server.app.core.retrieval.evidence_gate import EvidenceGate
from tests.factories.retrieval import build_scored_chunk


pytestmark = [pytest.mark.unit]


def test_evidence_gate_accepts_strong_aligned_evidence() -> None:
    gate = EvidenceGate(min_score=0.22, min_chunks=1)
    results = [build_scored_chunk("a", topic="stress_anxiety", score=0.7)]
    assert gate.has_enough_evidence(results, topic="stress_anxiety")


def test_evidence_gate_rejects_weak_and_misaligned_evidence() -> None:
    gate = EvidenceGate(min_score=0.22, min_chunks=1)
    weak = [build_scored_chunk("a", topic="stress_anxiety", score=0.1)]
    mismatch = [build_scored_chunk("b", topic="low_mood", score=0.8)]
    assert not gate.has_enough_evidence(weak, topic="stress_anxiety")
    assert not gate.has_enough_evidence(mismatch, topic="stress_anxiety")


def test_evidence_gate_allows_general_topic_without_alignment() -> None:
    gate = EvidenceGate(min_score=0.22, min_chunks=1)
    results = [build_scored_chunk("c", topic="stress_anxiety", score=0.7)]
    assert gate.has_enough_evidence(results, topic="general")


def test_gate_score_returns_zero_for_empty_results() -> None:
    assert EvidenceGate().gate_score([]) == 0.0


def test_evidence_gate_rejects_disallowed_use() -> None:
    gate = EvidenceGate(min_score=0.22, min_chunks=1)
    results = [
        build_scored_chunk(
            "a",
            topic="stress_anxiety",
            score=0.8,
            allowed_use=["psychoeducation"],
        )
    ]

    assert not gate.has_enough_evidence(
        results,
        topic="stress_anxiety",
        intent="coping_strategy",
        allowed_use=["coping_strategy"],
    )


def test_evidence_gate_rejects_low_evidence_level_for_strong_claims() -> None:
    gate = EvidenceGate(min_score=0.22, min_chunks=1)
    results = [
        build_scored_chunk(
            "a",
            topic="stress_anxiety",
            score=0.8,
            evidence_level="low_confidence",
        )
    ]

    assert not gate.has_enough_evidence(
        results,
        topic="stress_anxiety",
        min_evidence_level="educational",
    )


def test_evidence_gate_requires_matching_clinical_scope() -> None:
    gate = EvidenceGate(min_score=0.22, min_chunks=1)
    results = [
        build_scored_chunk(
            "crisis",
            topic="help_seeking",
            score=0.9,
            allowed_use=["crisis"],
            risk_level="crisis",
            clinical_scope="crisis_support_only",
            evidence_level="clinical_guideline",
        )
    ]

    assert not gate.has_enough_evidence(
        results,
        topic="help_seeking",
        intent="psychoeducation",
        allowed_use=["psychoeducation"],
        risk_level="none",
        clinical_scope="psychoeducation_only",
    )
    assert gate.has_enough_evidence(
        results,
        topic="help_seeking",
        intent="crisis",
        allowed_use=["crisis"],
        risk_level="crisis",
        clinical_scope="crisis_support_only",
    )
