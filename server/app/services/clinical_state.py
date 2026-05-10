from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.models.sql.models import UserClinicalState


def next_required_step(state: UserClinicalState | None) -> str:
    if state is None:
        return "screening"
    if not state.screening_completed:
        return "screening"
    return "chat"


async def get_or_create_clinical_state(db: AsyncSession, user_id: int) -> UserClinicalState:
    result = await db.execute(select(UserClinicalState).where(UserClinicalState.user_id == user_id))
    state = result.scalar_one_or_none()
    if state is not None:
        return state

    state = UserClinicalState(user_id=user_id)
    db.add(state)
    await db.flush()
    return state


async def mark_screening_complete(
    db: AsyncSession,
    user_id: int,
    *,
    phq9_score: int,
    gad7_score: int,
    completed_at: datetime | None = None,
) -> UserClinicalState:
    state = await get_or_create_clinical_state(db, user_id)
    timestamp = completed_at or datetime.now(timezone.utc)

    state.onboarding_completed = True
    state.screening_completed = True
    state.last_phq9_score = phq9_score
    state.last_gad7_score = gad7_score
    state.last_screening_date = timestamp
    state.screening_completed_at = timestamp
    state.onboarding_completed_at = timestamp
    return state
