from __future__ import annotations

import pytest
from sqlalchemy import select

from server.app.models.sql.models import MemoryReflection, MemorySegment
from server.app.services.memory_store import memory_extractor, memory_store


pytestmark = [pytest.mark.unit, pytest.mark.anyio]


def test_memory_extractor_captures_episodic_and_reflective_signals() -> None:
    extracted = memory_extractor.extract(
        "I feel lonely even when I am around people. This week I have been overwhelmed at work.",
        "Let's try grounding and a short walk tonight.",
        current_memory="Topic: loneliness",
    )

    assert extracted.episodic_events
    assert any("lonely" in item.lower() or "overwhelmed" in item.lower() for item in extracted.episodic_events)
    assert extracted.reflective_insights
    assert any("grounding" in item.lower() or "walk" in item.lower() for item in extracted.reflective_insights)


async def test_memory_store_persists_profile_episodic_and_reflection_segments(db_session_factory, authenticated_user) -> None:
    extracted = memory_extractor.extract(
        "I usually prefer short, direct answers and I feel stuck with exams.",
        "Let's focus on a walk and breathing first.",
        current_memory="Topic: stress",
    )

    async with db_session_factory() as db:
        await memory_store.add_segments(
            db,
            user_id=authenticated_user.id,
            session_id=12,
            topic="stress_anxiety",
            extracted=extracted,
        )
        await db.commit()

        segments = list((await db.execute(select(MemorySegment).where(MemorySegment.user_id == authenticated_user.id))).scalars())
        reflections = list((await db.execute(select(MemoryReflection).where(MemoryReflection.user_id == authenticated_user.id))).scalars())

        assert segments
        assert any(segment.segment_type == "profile_fact" for segment in segments)
        assert any(segment.segment_type == "episodic" for segment in segments)
        assert any(segment.topic == "stress_anxiety" for segment in segments)
        assert reflections
        assert any("support_preference" == reflection.insight_type for reflection in reflections)
