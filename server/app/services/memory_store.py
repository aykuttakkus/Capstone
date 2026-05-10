from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.models.sql.models import MemoryReflection, MemorySegment
from server.app.services.session import compact_memory_text
from server.app.utils.text import normalize_text


@dataclass(slots=True)
class ExtractedMemory:
    profile_facts: list[str] = field(default_factory=list)
    episodic_events: list[str] = field(default_factory=list)
    reflective_insights: list[str] = field(default_factory=list)
    legacy_summary: str = ""


def _line_has_signal(line: str) -> bool:
    lowered = normalize_text(line)
    return any(
        token in lowered
        for token in [
            "anxiety",
            "stress",
            "sleep",
            "panic",
            "burnout",
            "relationship",
            "help",
            "support",
            "exam",
            "family",
            "coping",
            "journal",
        ]
    )


class MemoryExtractionService:
    def extract(self, user_msg: str, ai_msg: str, current_memory: str = "") -> ExtractedMemory:
        lines = [line.strip() for line in user_msg.splitlines() if line.strip()]
        profile_facts: list[str] = []
        episodic_events: list[str] = []
        reflective_insights: list[str] = []

        for line in lines[:3]:
            if _line_has_signal(line):
                episodic_events.append(compact_memory_text(line, max_chars=220))

        normalized_user = normalize_text(user_msg)
        if "prefer" in normalized_user or "short" in normalized_user or "direct" in normalized_user:
            profile_facts.append(compact_memory_text(user_msg, max_chars=180))

        normalized_ai = normalize_text(ai_msg)
        if "breath" in normalized_ai or "ground" in normalized_ai or "journal" in normalized_ai:
            reflective_insights.append(
                compact_memory_text(f"Previously suggested support approach: {ai_msg}", max_chars=200)
            )

        legacy_bits = [bit for bit in [current_memory, *episodic_events, *reflective_insights] if bit]
        legacy_summary = "\n".join(legacy_bits[:4]).strip()
        return ExtractedMemory(
            profile_facts=profile_facts[:2],
            episodic_events=episodic_events[:3],
            reflective_insights=reflective_insights[:2],
            legacy_summary=legacy_summary,
        )


class MemoryStoreService:
    async def add_segments(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        session_id: int | None,
        topic: str | None,
        extracted: ExtractedMemory,
    ) -> None:
        for content in extracted.profile_facts:
            db.add(
                MemorySegment(
                    user_id=user_id,
                    session_id=session_id,
                    segment_type="profile_fact",
                    content=content,
                    topic=topic,
                    confidence=0.72,
                    source_turn_range="latest",
                )
            )
        for content in extracted.episodic_events:
            db.add(
                MemorySegment(
                    user_id=user_id,
                    session_id=session_id,
                    segment_type="episodic",
                    content=content,
                    topic=topic,
                    confidence=0.78,
                    source_turn_range="latest",
                )
            )
        for content in extracted.reflective_insights:
            db.add(
                MemoryReflection(
                    user_id=user_id,
                    insight_type="support_preference",
                    content=content,
                    evidence_refs=json.dumps({"session_id": session_id}),
                    confidence=0.68,
                    updated_at=datetime.now(timezone.utc),
                )
            )
        await db.flush()

    async def recent_segments(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        topic: str | None = None,
        limit: int = 5,
    ) -> list[MemorySegment]:
        stmt = select(MemorySegment).where(MemorySegment.user_id == user_id, MemorySegment.archived_at.is_(None))
        if topic:
            stmt = stmt.where((MemorySegment.topic == topic) | (MemorySegment.segment_type == "profile_fact"))
        result = await db.execute(stmt.order_by(desc(MemorySegment.created_at)).limit(limit))
        return list(result.scalars().all())

    async def reflections(self, db: AsyncSession, *, user_id: int, limit: int = 3) -> list[MemoryReflection]:
        result = await db.execute(
            select(MemoryReflection)
            .where(MemoryReflection.user_id == user_id)
            .order_by(desc(MemoryReflection.updated_at))
            .limit(limit)
        )
        return list(result.scalars().all())


memory_extractor = MemoryExtractionService()
memory_store = MemoryStoreService()
