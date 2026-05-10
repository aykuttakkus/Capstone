from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.core.database import get_db
from server.app.core.security import get_current_user
from server.app.models.schemas.feedback import FeedbackCreate, FeedbackRead
from server.app.models.sql.models import User
from server.app.services.feedback_store import create_feedback, list_feedback_for_user


router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("/", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
async def create_feedback_route(
    payload: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FeedbackRead:
    entry = await create_feedback(
        db,
        user_id=current_user.id,
        session_id=payload.session_id,
        message_id=payload.message_id,
        route=payload.route,
        helpful=payload.helpful,
        comment=payload.comment,
    )
    await db.commit()
    return FeedbackRead.model_validate(entry)


@router.get("/", response_model=list[FeedbackRead])
async def list_feedback_route(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FeedbackRead]:
    entries = await list_feedback_for_user(db, current_user.id)
    return [FeedbackRead.model_validate(entry) for entry in entries]
