from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.core.database import get_db
from server.app.core.security import get_current_user
from server.app.models.schemas.profile import ProfileSummary, UserProfileRead, UserProfileUpdate
from server.app.models.sql.models import User
from server.app.services.profile import profile_service


router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/", response_model=UserProfileRead)
async def read_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileRead:
    profile = await profile_service.get_or_create(db, current_user.id)
    await db.commit()
    return UserProfileRead.model_validate(profile)


@router.put("/", response_model=UserProfileRead)
async def update_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileRead:
    profile = await profile_service.get_or_create(db, current_user.id)
    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    profile.last_profile_refresh_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(profile)
    return UserProfileRead.model_validate(profile)


@router.get("/summary", response_model=ProfileSummary)
async def read_profile_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileSummary:
    profile = await profile_service.get_or_create(db, current_user.id)
    await db.commit()
    return ProfileSummary(
        snapshot=profile_service.summarize(profile),
        personalization_enabled=bool(profile.personalization_consent),
        context_sources=[
            source
            for source, enabled in [
                ("profile", True),
                ("memory", profile.use_memory_context),
                ("mood", profile.use_mood_context),
                ("journal", profile.use_journal_context),
            ]
            if enabled
        ],
    )
