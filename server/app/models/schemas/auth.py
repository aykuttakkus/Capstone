from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from server.app.models.schemas.profile import UserProfileRead


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserLogin(UserBase):
    password: str


class ClinicalStateRead(BaseModel):
    onboarding_completed: bool = False
    screening_completed: bool = False
    last_phq9_score: Optional[int] = None
    last_gad7_score: Optional[int] = None
    last_screening_date: Optional[datetime] = None
    screening_completed_at: Optional[datetime] = None
    onboarding_completed_at: Optional[datetime] = None
    next_required_step: str = "screening"

    model_config = ConfigDict(from_attributes=True)


class UserRead(UserBase):
    id: int
    created_at: datetime
    last_phq9_score: Optional[int] = None
    last_gad7_score: Optional[int] = None
    onboarding_completed: bool = False
    screening_completed: bool = False
    next_required_step: str = "screening"
    clinical_state: Optional[ClinicalStateRead] = None
    profile: Optional[UserProfileRead] = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
