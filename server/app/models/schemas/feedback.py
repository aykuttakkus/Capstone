from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FeedbackCreate(BaseModel):
    session_id: int | None = None
    message_id: int | None = None
    route: str | None = None
    helpful: bool
    comment: str | None = None


class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    session_id: int | None = None
    message_id: int | None = None
    route: str | None = None
    helpful: str
    comment: str | None = None
    created_at: datetime
