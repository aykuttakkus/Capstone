from __future__ import annotations

import pytest
from sqlalchemy import select

from server.app.models.sql.models import ChatMessage, ChatSession, User


pytestmark = [pytest.mark.integration, pytest.mark.anyio]


async def test_sqlite_models_persist_and_reload(db_session_factory) -> None:
    async with db_session_factory() as db:
        user = User(email="persist@example.com", hashed_password="hashed")
        db.add(user)
        await db.flush()

        session = ChatSession(user_id=user.id, title="Session", topic="stress_anxiety", status="active")
        db.add(session)
        await db.flush()

        db.add(
            ChatMessage(
                session_id=session.id,
                user_id=user.id,
                role="assistant",
                content="Source-backed answer",
                intent="psychoeducation",
                route="topic:stress_anxiety",
                safety_mode="normal",
            )
        )
        await db.commit()

        loaded_user = (await db.execute(select(User).where(User.email == "persist@example.com"))).scalar_one()
        loaded_session = (await db.execute(select(ChatSession).where(ChatSession.user_id == loaded_user.id))).scalar_one()
        loaded_message = (await db.execute(select(ChatMessage).where(ChatMessage.session_id == loaded_session.id))).scalar_one()

        assert loaded_session.topic == "stress_anxiety"
        assert loaded_message.content == "Source-backed answer"
