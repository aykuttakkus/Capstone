from __future__ import annotations

from types import SimpleNamespace

import pytest

from server.app.services.memory_context import build_memory_bundle
from server.app.services.memory_observability import build_memory_observability_report, serialize_memory_observability


pytestmark = [pytest.mark.unit]


def test_memory_observability_report_serializes_key_fields() -> None:
    bundle = build_memory_bundle(
        session_summary="Topic: stress_anxiety.",
        user_memory="Preferred name: Aykut",
        recent_segments=[SimpleNamespace(content="User prefers short answers", topic="general", confidence=0.9)],
        history=[{"role": "user", "content": "I feel overwhelmed"}],
        current_message="I feel overwhelmed",
        topic="stress_anxiety",
    )

    report = build_memory_observability_report(
        bundle=bundle,
        confidence=0.72,
        evidence_status="partially_supported",
        conversation_mode="explain",
        profile_used=True,
        mood_used=False,
        journal_used=False,
    )

    payload = serialize_memory_observability(report)

    assert payload["topic"] == "stress_anxiety"
    assert payload["selected_memory_count"] >= 1
    assert payload["confidence"] == 0.72
    assert payload["evidence_status"] == "partially_supported"
