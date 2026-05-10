from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: int | None = None
    new_session: bool = False
    intake: dict[str, Any] = Field(default_factory=dict)
    screening: dict[str, Any] = Field(default_factory=dict)
    history: list[dict[str, Any]] = Field(default_factory=list)
    personalization: dict[str, Any] = Field(default_factory=dict)


class SourceReference(BaseModel):
    title: str
    source: str
    topic: str
    score: float
    excerpt: str
    rank: int | None = None
    source_kind: str | None = None
    language: str | None = None
    confidence: float | None = None
    section: str | None = None
    page: int | None = None
    reason_tags: list[str] = Field(default_factory=list)


class RetrievalDiagnostic(BaseModel):
    rank: int
    chunk_id: str
    title: str
    topic: str
    score: float
    source_kind: str | None = None
    language: str | None = None
    confidence: float | None = None
    topic_alignment: str
    query_overlap: int
    reason_tags: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    session_id: int | None = None
    status: str
    route: str
    intent: str
    safety_mode: str
    summary: str
    answer: str
    follow_up: list[str] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)
    retrieval_diagnostics: list[RetrievalDiagnostic] = Field(default_factory=list)
    source_highlight: str | None = None
    personalization_applied: bool = False
    personalization_signals: list[str] = Field(default_factory=list)
    context_used: dict[str, bool] = Field(default_factory=dict)
    care_plan_hint: str | None = None
    clinical_nugget: str | None = None
