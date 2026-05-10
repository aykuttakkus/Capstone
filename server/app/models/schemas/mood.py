from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MoodEntryCreate(BaseModel):
    mood_score: int = Field(ge=1, le=10)
    energy_score: int | None = Field(default=None, ge=1, le=10)
    anxiety_score: int | None = Field(default=None, ge=1, le=10)
    sleep_quality: int | None = Field(default=None, ge=1, le=10)
    notes: str | None = None


class MoodEntryRead(MoodEntryCreate):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MoodTrendRead(BaseModel):
    summary: str
    recent_average_mood: float | None = None
    recent_average_anxiety: float | None = None
    pattern_tags: list[str] = Field(default_factory=list)
    entries: list[MoodEntryRead] = Field(default_factory=list)
