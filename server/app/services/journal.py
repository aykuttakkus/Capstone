from __future__ import annotations

import json

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.models.schemas.journal import JournalInsightRead
from server.app.models.sql.models import JournalEntry
from server.app.utils.text import normalize_text


def _infer_topics(text: str) -> list[str]:
    lowered = normalize_text(text)
    topics: list[str] = []
    mapping = {
        "stress_anxiety": ["stress", "anxiety", "panic", "worry", "kaygi"],
        "burnout_sleep": ["sleep", "tired", "fatigue", "burnout", "uyku"],
        "low_mood": ["sad", "low mood", "hopeless", "depressed"],
        "social_pressure": ["family", "relationship", "friend", "social"],
    }
    for topic, keywords in mapping.items():
        if any(keyword in lowered for keyword in keywords):
            topics.append(topic)
    return topics or ["general"]


class JournalInsightService:
    def _sentiment_label(self, content: str) -> str:
        lowered = normalize_text(content)
        if any(token in lowered for token in ["panic", "hopeless", "overwhelmed", "exhausted"]):
            return "distressed"
        if any(token in lowered for token in ["anxiety", "stress", "worried", "tired"]):
            return "concerned"
        if any(token in lowered for token in ["calm", "better", "relieved", "hopeful"]):
            return "steady"
        return "neutral"

    async def create_entry(self, db: AsyncSession, user_id: int, *, title: str | None, content: str, consent_for_chat: bool) -> JournalEntry:
        sentiment_label = self._sentiment_label(content)
        risk_flag = any(token in normalize_text(content) for token in ["suicide", "self harm", "hurt myself"])
        entry = JournalEntry(
            user_id=user_id,
            title=title,
            content=content,
            consent_for_chat=consent_for_chat,
            sentiment_label=sentiment_label,
            topics_json=json.dumps(_infer_topics(content)),
            risk_flag=risk_flag,
        )
        db.add(entry)
        await db.flush()
        return entry

    async def list_entries(self, db: AsyncSession, user_id: int, limit: int = 10) -> list[JournalEntry]:
        result = await db.execute(
            select(JournalEntry).where(JournalEntry.user_id == user_id).order_by(desc(JournalEntry.created_at)).limit(limit)
        )
        return list(result.scalars().all())

    async def build_insights(self, db: AsyncSession, user_id: int, limit: int = 10) -> JournalInsightRead:
        entries = await self.list_entries(db, user_id, limit=limit)
        if not entries:
            return JournalInsightRead(summary="", entries=[])

        theme_counts: dict[str, int] = {}
        consented = [entry for entry in entries if entry.consent_for_chat]
        for entry in consented:
            for topic in json.loads(entry.topics_json or "[]"):
                theme_counts[topic] = theme_counts.get(topic, 0) + 1
        repeated_themes = [topic for topic, count in sorted(theme_counts.items(), key=lambda item: item[1], reverse=True)[:3]]
        summary = ""
        if repeated_themes:
            summary = f"Recent journal themes include {', '.join(repeated_themes)}."

        return JournalInsightRead(
            summary=summary,
            repeated_themes=repeated_themes,
            entries=[
                type("JournalEntryProxy", (), {
                    "id": entry.id,
                    "user_id": entry.user_id,
                    "title": entry.title,
                    "content": entry.content,
                    "consent_for_chat": entry.consent_for_chat,
                    "sentiment_label": entry.sentiment_label,
                    "topics": json.loads(entry.topics_json or "[]"),
                    "risk_flag": entry.risk_flag,
                    "created_at": entry.created_at,
                })()
                for entry in entries
            ],
        )


journal_service = JournalInsightService()
