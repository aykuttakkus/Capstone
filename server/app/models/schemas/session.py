from __future__ import annotations

from typing import Any
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SessionMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    intent: str | None = None
    route: str | None = None
    safety_mode: str | None = None
    created_at: datetime


class SessionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    topic: str | None = None
    status: str
    last_safety_mode: str | None = None
    created_at: datetime
    last_message_at: datetime | None = None
    archived_at: datetime | None = None


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    topic: str | None = None
    status: str
    summary: str | None = None
    last_safety_mode: str | None = None
    intake: dict[str, Any] | None = None
    consent: dict[str, Any] | None = None
    created_at: datetime
    last_message_at: datetime | None = None
    archived_at: datetime | None = None
    messages: list[SessionMessageRead] = Field(default_factory=list)
