from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.core.database import get_db
from server.app.core.security import get_current_user
from server.app.models.schemas.journal import JournalEntryCreate, JournalEntryRead, JournalInsightRead
from server.app.models.sql.models import User
from server.app.services.journal import journal_service


router = APIRouter(prefix="/journal", tags=["Journal"])


def _to_read(entry) -> JournalEntryRead:
    return JournalEntryRead(
        id=entry.id,
        user_id=entry.user_id,
        title=entry.title,
        content=entry.content,
        consent_for_chat=entry.consent_for_chat,
        sentiment_label=entry.sentiment_label,
        topics=json.loads(entry.topics_json or "[]"),
        risk_flag=entry.risk_flag,
        created_at=entry.created_at,
    )


@router.get("/", response_model=list[JournalEntryRead])
async def list_journal_entries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[JournalEntryRead]:
    entries = await journal_service.list_entries(db, current_user.id)
    return [_to_read(entry) for entry in entries]


@router.post("/", response_model=JournalEntryRead)
async def create_journal_entry(
    payload: JournalEntryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JournalEntryRead:
    entry = await journal_service.create_entry(db, current_user.id, **payload.model_dump())
    await db.commit()
    await db.refresh(entry)
    return _to_read(entry)


@router.get("/insights", response_model=JournalInsightRead)
async def read_journal_insights(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JournalInsightRead:
    return await journal_service.build_insights(db, current_user.id)
