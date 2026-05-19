from __future__ import annotations

import pytest
from sqlalchemy import select

from server.app.models.sql.models import Memory, MemoryReflection, MemorySegment, UserProfile
from server.app.services.profile import profile_service


pytestmark = [pytest.mark.unit, pytest.mark.anyio]


async def test_profile_service_respects_no_personalization_consent(db_session_factory, authenticated_user) -> None:
    async with db_session_factory() as db:
        profile = await profile_service.refresh_from_context(
            db,
            authenticated_user.id,
            intake={"communication_style": "direct", "response_length_preference": "short"},
            personalization={"preferred_name": "Aykut", "personalization_consent": False, "use_memory_context": True},
        )

        assert profile.personalization_consent is False
        assert profile.preferred_name is None
        assert profile.communication_style is None
        assert profile.response_length_preference is None


async def test_assistant_service_skips_long_term_memory_when_consent_is_off(
    db_session_factory,
    authenticated_user,
    mock_llm_backend,
) -> None:
    from tests.unit.services.test_assistant_service import FakePlan, build_service, build_scored_chunk

    service = build_service(
        plan=FakePlan(
            route="topic:stress_anxiety",
            topic="stress_anxiety",
            intent="psychoeducation",
            safety_mode="normal",
            risk_level=0,
        ),
        retrievals=[build_scored_chunk("stress-001", topic="stress_anxiety", score=0.91)],
        grader_flags=[True],
        llm_backend=mock_llm_backend,
    )

    async with db_session_factory() as db:
        response = await service.handle_message(
            message="I feel lonely even when I am around people",
            user=authenticated_user,
            db=db,
            intake={},
            screening={},
            history=[],
            personalization={"personalization_consent": False, "use_memory_context": True},
        )

        memory_rows = list((await db.execute(select(Memory))).scalars())
        segment_rows = list((await db.execute(select(MemorySegment))).scalars())
        reflection_rows = list((await db.execute(select(MemoryReflection))).scalars())
        profile_rows = list((await db.execute(select(UserProfile))).scalars())

        assert response.status == "grounded"
        assert memory_rows == []
        assert segment_rows == []
        assert reflection_rows == []
        assert profile_rows[0].preferred_name is None


async def test_crisis_short_circuit_does_not_write_long_term_memory(
    db_session_factory,
    authenticated_user,
    offline_llm_backend,
) -> None:
    from tests.unit.services.test_assistant_service import FakePlan, build_service

    service = build_service(
        plan=FakePlan(
            route="crisis_support",
            topic="stress_anxiety",
            intent="emotional_support",
            safety_mode="crisis_support",
            risk_level=3,
            immediate_response="Please contact emergency support now.",
        ),
        retrievals=[],
        grader_flags=[],
        llm_backend=offline_llm_backend,
    )

    async with db_session_factory() as db:
        response = await service.handle_message(
            message="I want to die and I am not safe right now.",
            user=authenticated_user,
            db=db,
            intake={},
            screening={},
            history=[],
        )

        memory_rows = list((await db.execute(select(Memory))).scalars())
        segment_rows = list((await db.execute(select(MemorySegment))).scalars())

        assert response.status == "crisis"
        assert memory_rows == []
        assert segment_rows == []
