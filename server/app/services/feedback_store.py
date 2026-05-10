from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.models.sql.models import FeedbackEntry


async def create_feedback(
    db: AsyncSession,
    *,
    user_id: int,
    session_id: int | None,
    message_id: int | None,
    route: str | None,
    helpful: bool,
    comment: str | None,
) -> FeedbackEntry:
    entry = FeedbackEntry(
        user_id=user_id,
        session_id=session_id,
        message_id=message_id,
        route=route,
        helpful="yes" if helpful else "no",
        comment=comment,
    )
    db.add(entry)
    await db.flush()
    return entry


async def list_feedback_for_user(db: AsyncSession, user_id: int, limit: int = 50) -> list[FeedbackEntry]:
    result = await db.execute(
        select(FeedbackEntry)
        .where(FeedbackEntry.user_id == user_id)
        .order_by(FeedbackEntry.created_at.desc())
        .limit(max(1, min(limit, 100)))
    )
    return list(result.scalars().all())
