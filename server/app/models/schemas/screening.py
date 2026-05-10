from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ScreeningRequest(BaseModel):
    test_type: Literal["phq9", "gad7"]
    answers: dict[str, int] = Field(default_factory=dict)


class ScreeningResponse(BaseModel):
    scale_name: str
    score: int
    severity: str
    crisis_flag: bool
