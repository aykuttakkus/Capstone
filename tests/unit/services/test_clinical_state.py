from __future__ import annotations

from datetime import datetime, timezone

import pytest

from server.app.services.clinical_state import get_or_create_clinical_state, mark_screening_complete, next_required_step


pytestmark = [pytest.mark.unit, pytest.mark.anyio]


async def test_clinical_state_defaults_to_screening_then_advances_to_chat(
    db_session_factory,
    authenticated_user,
) -> None:
    async with db_session_factory() as db:
        state = await get_or_create_clinical_state(db, authenticated_user.id)
        assert state.screening_completed is False
        assert next_required_step(state) == "screening"

        timestamp = datetime.now(timezone.utc)
        updated = await mark_screening_complete(
            db,
            authenticated_user.id,
            phq9_score=5,
            gad7_score=4,
            completed_at=timestamp,
        )
        await db.commit()

        assert updated.screening_completed is True
        assert updated.onboarding_completed is True
        assert updated.last_gad7_score == 4
        assert next_required_step(updated) == "chat"
