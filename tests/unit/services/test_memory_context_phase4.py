from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from server.app.services.memory_context import build_memory_bundle


pytestmark = [pytest.mark.unit]


def _segment(content: str, topic: str, confidence: float, age_days: int = 0):
    return SimpleNamespace(
        content=content,
        topic=topic,
        confidence=confidence,
        created_at=datetime.now(timezone.utc) - timedelta(days=age_days),
    )


def _naive_segment(content: str, topic: str, confidence: float):
    return SimpleNamespace(
        content=content,
        topic=topic,
        confidence=confidence,
        created_at=datetime.utcnow(),
    )


def test_memory_bundle_ranks_relevant_items_above_irrelevant_noise() -> None:
    bundle = build_memory_bundle(
        session_summary="Topic: loneliness.",
        user_memory="Preferred name: Aykut",
        recent_segments=[
            _segment("User feels lonely even around people", "low_mood", 0.85, age_days=0),
            _segment("User prefers short answers", "general", 0.95, age_days=1),
            _segment("Irrelevant cooking hobby", "general", 0.2, age_days=0),
            _segment("Work stress has worsened sleep", "stress_anxiety", 0.88, age_days=2),
        ],
        reflections=[
            _segment("Grounding and short walks helped", "low_mood", 0.7, age_days=0),
        ],
        history=[{"role": "user", "content": "I feel lonely even when I am around people"}],
        current_message="I feel lonely even when I am around people",
        topic="low_mood",
        safety_mode="normal",
    )

    selected_texts = [item.content for item in bundle.selected_memory_items]

    assert any("lonely" in text.lower() for text in selected_texts)
    assert any("grounding" in text.lower() or "walk" in text.lower() for text in selected_texts)
    assert not any("cooking hobby" in text.lower() for text in selected_texts)
    assert bundle.debug["selected_memory_count"] == len(bundle.selected_memory_items)
    assert bundle.debug["selected_segment_scores"]
    assert bundle.selected_memory_items[0].score >= bundle.selected_memory_items[-1].score


def test_memory_bundle_uses_message_overlap_to_promote_relevant_memory() -> None:
    bundle = build_memory_bundle(
        session_summary="Topic: stress.",
        user_memory="Preferred name: Aykut",
        recent_segments=[
            _segment("I am overwhelmed by exams", "stress_anxiety", 0.5, age_days=2),
            _segment("I like to keep answers short", "general", 0.8, age_days=1),
        ],
        reflections=[],
        history=[{"role": "user", "content": "The exams are overwhelming me"}],
        current_message="The exams are overwhelming me",
        topic="stress_anxiety",
    )

    assert bundle.selected_memory_items
    assert "overwhelmed" in bundle.selected_memory_items[0].content.lower()
    assert "[Recent Turns:" in bundle.prompt_context


def test_memory_bundle_handles_naive_timestamps_without_crashing() -> None:
    bundle = build_memory_bundle(
        session_summary="Topic: stress.",
        user_memory="Preferred name: Aykut",
        recent_segments=[_naive_segment("I am overwhelmed by exams", "stress_anxiety", 0.5)],
        reflections=[_naive_segment("Grounding and short walks helped", "stress_anxiety", 0.7)],
        history=[{"role": "user", "content": "The exams are overwhelming me"}],
        current_message="The exams are overwhelming me",
        topic="stress_anxiety",
    )

    assert bundle.selected_memory_items
