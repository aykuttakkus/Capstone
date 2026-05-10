from __future__ import annotations

from dataclasses import dataclass, field

from server.app.core.agents.sentiment_agent import SentimentProfile
from server.app.models.sql.models import MemoryReflection, MemorySegment, UserProfile


@dataclass(slots=True)
class PersonalizedQuery:
    retrieval_query: str
    retrieval_filters: dict[str, str] = field(default_factory=dict)
    reason_context: str = ""


class PersonalizedQueryBuilder:
    def build(
        self,
        *,
        message: str,
        topic: str,
        profile: UserProfile | None,
        screening: dict[str, object] | None,
        memory_segments: list[MemorySegment],
        reflections: list[MemoryReflection],
        sentiment: SentimentProfile | None,
    ) -> PersonalizedQuery:
        parts = [message.strip()]
        reasons: list[str] = []
        if profile and profile.primary_concerns:
            parts.append(f"Primary concern: {profile.primary_concerns}")
            reasons.append("profile_primary_concern")
        if profile and profile.goals_for_support:
            parts.append(f"Support goal: {profile.goals_for_support}")
            reasons.append("profile_support_goal")
        if screening and screening.get("severity"):
            parts.append(f"Screening context: {screening.get('severity')}")
            reasons.append("screening")
        if sentiment and sentiment.label:
            parts.append(f"Emotion: {sentiment.label}")
            reasons.append("sentiment")
        for segment in memory_segments[:2]:
            parts.append(f"Relevant prior context: {segment.content}")
            reasons.append(f"memory:{segment.segment_type}")
        for reflection in reflections[:1]:
            parts.append(f"Previously useful approach: {reflection.content}")
            reasons.append(f"reflection:{reflection.insight_type}")
        # Professional Standard: Use ONLY the core message for vector retrieval 
        # to avoid noise from legacy profile/screening data.
        retrieval_query = message.strip()
        
        return PersonalizedQuery(
            retrieval_query=retrieval_query,
            retrieval_filters={"topic": topic},
            reason_context=", ".join(reasons),
        )


query_builder = PersonalizedQueryBuilder()
