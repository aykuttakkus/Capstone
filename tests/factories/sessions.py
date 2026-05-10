from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from server.app.models.sql.models import ChatSession, User
from server.app.services.session_store import append_session_turn, ensure_session


async def create_session_with_turn(
    db: AsyncSession,
    user: User,
    *,
    title: str = "Stress support",
    topic: str = "stress_anxiety",
    query: str = "I feel overwhelmed",
    response: str = "Let us look at stress basics.",
    route: str = "topic:stress_anxiety",
    safety_mode: str = "normal",
) -> ChatSession:
    session = await ensure_session(
        db,
        user.id,
        title=title,
        topic=topic,
        intake={"main_issue": "stress"},
        consent={"screening": True},
    )
    await append_session_turn(
        db,
        session,
        user.id,
        query=query,
        response=response,
        intent="psychoeducation",
        route=route,
        safety_mode=safety_mode,
        sources=[
            {
                "title": "Stress basics",
                "source": "Test corpus",
                "topic": topic,
                "score": 0.91,
                "excerpt": "Stress affects sleep and energy.",
            }
        ],
        intake={"main_issue": "stress", "help_type": "Sources"},
    )
    await db.commit()
    await db.refresh(session)
    return session
