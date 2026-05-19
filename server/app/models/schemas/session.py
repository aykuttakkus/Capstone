from __future__ import annotations

from typing import Any
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SessionSummarySchema(BaseModel):
    """Spec §31 compliant structured session summary — 9 mandatory fields."""

    main_concern: str = ""
    emotional_state: str = "neutral"
    triggers: list[str] = Field(default_factory=list)
    coping_tried: list[str] = Field(default_factory=list)
    coping_effectiveness: dict[str, str] = Field(default_factory=dict)
    user_goal: str = ""
    risk_state: dict[str, Any] = Field(default_factory=dict)
    last_response_mode: str = ""
    important_new_information: list[str] = Field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "SessionSummarySchema":
        """Safely coerce a raw dict (possibly partial) into the schema."""
        if not data:
            return cls()
        return cls(**{k: v for k, v in data.items() if k in cls.model_fields})


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
