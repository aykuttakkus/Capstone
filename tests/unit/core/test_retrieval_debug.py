from __future__ import annotations

import pytest

from server.app.services.retrieval_debug import build_retrieval_diagnostics, build_source_reference
from tests.factories.retrieval import build_scored_chunk


pytestmark = [pytest.mark.unit]


def test_source_reference_includes_rank_excerpt_and_reason_tags() -> None:
    scored = build_scored_chunk("stress-001", topic="stress_anxiety", score=0.91)
    reference = build_source_reference(
        "Tell me about stress and sleep",
        scored,
        rank=1,
        query_topic="stress_anxiety",
    )

    assert reference.rank == 1
    assert reference.excerpt.startswith("Stress can affect")
    assert "topic_match" in reference.reason_tags


def test_retrieval_diagnostics_expose_alignment_and_overlap() -> None:
    diagnostics = build_retrieval_diagnostics(
        "Tell me about stress and sleep",
        [
            build_scored_chunk("stress-001", topic="stress_anxiety", score=0.93),
            build_scored_chunk("sleep-001", topic="burnout_sleep", score=0.72),
        ],
        query_topic="stress_anxiety",
    )

    assert diagnostics[0].topic_alignment == "exact"
    assert diagnostics[0].query_overlap > 0
    assert diagnostics[1].reason_tags
