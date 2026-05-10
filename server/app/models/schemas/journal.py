from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JournalEntryCreate(BaseModel):
    title: str | None = None
    content: str = Field(min_length=1)
    consent_for_chat: bool = False


class JournalEntryRead(JournalEntryCreate):
    id: int
    user_id: int
    sentiment_label: str | None = None
    topics: list[str] = Field(default_factory=list)
    risk_flag: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JournalInsightRead(BaseModel):
    summary: str
    repeated_themes: list[str] = Field(default_factory=list)
    entries: list[JournalEntryRead] = Field(default_factory=list)
