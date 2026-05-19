from __future__ import annotations

from server.app.services.retrieval_debug import build_retrieval_diagnostics
from tests.factories.retrieval import build_scored_chunk


def test_retrieval_diagnostics_include_safety_scope_tags() -> None:
    retrievals = [
        build_scored_chunk(
            "crisis",
            topic="help_seeking",
            score=0.9,
            allowed_use=["crisis"],
            risk_level="crisis",
            clinical_scope="crisis_support_only",
            content_type="crisis_instruction",
        )
    ]

    diagnostics = build_retrieval_diagnostics("immediate danger", retrievals, query_topic="help_seeking")

    assert diagnostics[0].reason_tags
    assert "scope:crisis_support_only" in diagnostics[0].reason_tags
    assert "content:crisis_instruction" in diagnostics[0].reason_tags
