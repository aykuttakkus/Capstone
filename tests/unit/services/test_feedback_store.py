from __future__ import annotations

import pytest

from server.app.services.feedback_store import create_feedback, list_feedback_for_user


pytestmark = [pytest.mark.unit, pytest.mark.anyio]


async def test_feedback_store_roundtrip(db_session_factory, authenticated_user) -> None:
    async with db_session_factory() as db:
        entry = await create_feedback(
            db,
            user_id=authenticated_user.id,
            session_id=None,
            message_id=None,
            route="topic:stress_anxiety",
            helpful=True,
            comment="Clear answer.",
        )
        await db.commit()

        entries = await list_feedback_for_user(db, authenticated_user.id)
        assert len(entries) == 1
        assert entries[0].helpful == "yes"
        assert entry.comment == "Clear answer."
