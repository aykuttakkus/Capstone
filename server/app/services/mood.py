from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.models.schemas.mood import MoodTrendRead
from server.app.models.sql.models import MoodEntry


class MoodTrendService:
    async def create_entry(self, db: AsyncSession, user_id: int, **payload) -> MoodEntry:
        entry = MoodEntry(user_id=user_id, **payload)
        db.add(entry)
        await db.flush()
        return entry

    async def list_entries(self, db: AsyncSession, user_id: int, limit: int = 14) -> list[MoodEntry]:
        result = await db.execute(
            select(MoodEntry).where(MoodEntry.user_id == user_id).order_by(desc(MoodEntry.created_at)).limit(limit)
        )
        return list(result.scalars().all())

    async def build_trend(self, db: AsyncSession, user_id: int, limit: int = 14) -> MoodTrendRead:
        entries = await self.list_entries(db, user_id, limit=limit)
        if not entries:
            return MoodTrendRead(summary="", entries=[])

        avg_mood = sum(entry.mood_score for entry in entries) / len(entries)
        anxiety_values = [entry.anxiety_score for entry in entries if entry.anxiety_score is not None]
        avg_anxiety = sum(anxiety_values) / len(anxiety_values) if anxiety_values else None

        tags: list[str] = []
        if avg_mood <= 4:
            tags.append("low_mood_pattern")
        if avg_anxiety is not None and avg_anxiety >= 7:
            tags.append("high_anxiety_pattern")
        sleep_values = [entry.sleep_quality for entry in entries if entry.sleep_quality is not None]
        if sleep_values and (sum(sleep_values) / len(sleep_values)) <= 4:
            tags.append("sleep_strain")

        summary_parts = []
        if avg_mood <= 4:
            summary_parts.append("recent mood trend has been low")
        if avg_anxiety is not None and avg_anxiety >= 7:
            summary_parts.append("anxiety has remained elevated")
        if sleep_values and (sum(sleep_values) / len(sleep_values)) <= 4:
            summary_parts.append("sleep quality has also been strained")

        summary = ", and ".join(summary_parts).capitalize()
        return MoodTrendRead(
            summary=summary,
            recent_average_mood=round(avg_mood, 2),
            recent_average_anxiety=round(avg_anxiety, 2) if avg_anxiety is not None else None,
            pattern_tags=tags,
            entries=entries,
        )


mood_service = MoodTrendService()
