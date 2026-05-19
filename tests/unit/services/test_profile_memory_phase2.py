from __future__ import annotations

import pytest

from server.app.services.profile import profile_service


pytestmark = [pytest.mark.unit, pytest.mark.anyio]


async def test_profile_service_merges_stable_preferences_without_losing_existing_facts(db_session_factory, authenticated_user) -> None:
    async with db_session_factory() as db:
        profile = await profile_service.refresh_from_context(
            db,
            authenticated_user.id,
            intake={"communication_style": "direct", "response_length_preference": "short"},
            personalization={"preferred_name": "Aykut", "use_memory_context": True},
        )
        await db.commit()

        profile = await profile_service.refresh_from_context(
            db,
            authenticated_user.id,
            intake={"communication_style": "direct", "response_length_preference": "short"},
            personalization={"preferred_name": "Aykut", "use_memory_context": True},
        )

        assert profile.preferred_name == "Aykut"
        assert profile.communication_style == "direct"
        assert profile.response_length_preference == "short"


async def test_profile_service_keeps_transient_screening_context_out_of_stable_identity(db_session_factory, authenticated_user) -> None:
    async with db_session_factory() as db:
        profile = await profile_service.refresh_from_context(
            db,
            authenticated_user.id,
            intake={},
            screening={"severity": "mild"},
            personalization={},
        )

        assert profile.stress_context is not None
        assert "Recent self-screening context" in profile.stress_context
