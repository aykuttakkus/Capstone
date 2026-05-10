from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.core.database import get_db
from server.app.core.security import get_current_user
from server.app.models.schemas.mood import MoodEntryCreate, MoodEntryRead, MoodTrendRead
from server.app.models.sql.models import User
from server.app.services.mood import mood_service


router = APIRouter(prefix="/mood", tags=["Mood Tracking"])


@router.get("/", response_model=list[MoodEntryRead])
async def list_mood_entries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MoodEntryRead]:
    entries = await mood_service.list_entries(db, current_user.id)
    return [MoodEntryRead.model_validate(entry) for entry in entries]


@router.post("/", response_model=MoodEntryRead)
async def create_mood_entry(
    payload: MoodEntryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MoodEntryRead:
    entry = await mood_service.create_entry(db, current_user.id, **payload.model_dump())
    await db.commit()
    await db.refresh(entry)
    return MoodEntryRead.model_validate(entry)


@router.get("/trend", response_model=MoodTrendRead)
async def read_mood_trend(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MoodTrendRead:
    return await mood_service.build_trend(db, current_user.id)
