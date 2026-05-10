from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserProfileBase(BaseModel):
    preferred_name: str | None = None
    age_group: str | None = None
    therapy_status: str | None = None
    primary_concerns: str | None = None
    main_triggers: str | None = None
    support_system: str | None = None
    coping_strategies_helpful: str | None = None
    coping_strategies_unhelpful: str | None = None
    communication_style: str | None = None
    response_length_preference: str | None = None
    sleep_context: str | None = None
    stress_context: str | None = None
    goals_for_support: str | None = None
    life_narrative: str | None = None
    personalization_consent: bool = True
    use_mood_context: bool = False
    use_journal_context: bool = False
    use_memory_context: bool = True


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileRead(UserProfileBase):
    id: int
    user_id: int
    intake_completed: bool = False
    last_profile_refresh_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ProfileSummary(BaseModel):
    snapshot: str
    personalization_enabled: bool = True
    context_sources: list[str] = Field(default_factory=list)
