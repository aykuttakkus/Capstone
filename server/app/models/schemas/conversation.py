from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query: str
    response: str
    safety_mode: str | None = None
    latency_ms: float | None = None
    created_at: datetime
