from __future__ import annotations

from dataclasses import dataclass, field

from server.app.models.sql.models import MemoryReflection, MemorySegment, UserProfile


@dataclass(slots=True)
class SentimentProfile:
    label: str
    urgency: int
    empathy_required: bool
    rationale: str


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
        # Spec §13: context-aware query enrichment
        session_summary: dict[str, object] | None = None,
        primary_intent: str = "",
        secondary_intents: list[str] | None = None,
        risk_level: str = "none",
    ) -> PersonalizedQuery:
        query_parts = [message.strip()]
        reasons: list[str] = []

        # 1. Session summary enrichment (spec §13)
        if session_summary:
            if session_summary.get("main_concern"):
                query_parts.append(str(session_summary["main_concern"]))
                reasons.append("session_main_concern")
            triggers = session_summary.get("triggers")
            if isinstance(triggers, list) and triggers:
                query_parts.extend(str(t) for t in triggers[:2])
                reasons.append("session_triggers")

        # 2. Intent enrichment — only for information-seeking intents
        if primary_intent and primary_intent not in {"off_scope", "crisis", "repair", "emotional_support"}:
            query_parts.append(primary_intent.replace("_", " "))
            reasons.append("primary_intent")
        if secondary_intents:
            for intent in secondary_intents[:2]:
                if intent not in {"off_scope", "crisis"}:
                    query_parts.append(intent.replace("_", " "))
            reasons.append("secondary_intents")

        # 3. Profile enrichment
        if profile and profile.primary_concerns:
            query_parts.append(str(profile.primary_concerns))
            reasons.append("profile_primary_concern")

        # 4. Memory segment enrichment (brief excerpts to avoid noise)
        for segment in memory_segments[:2]:
            excerpt = str(segment.content)[:80]
            query_parts.append(excerpt)
            reasons.append(f"memory:{segment.segment_type}")
        for reflection in reflections[:1]:
            query_parts.append(str(reflection.content)[:60])
            reasons.append(f"reflection:{reflection.insight_type}")

        retrieval_query = " ".join(query_parts)

        return PersonalizedQuery(
            retrieval_query=retrieval_query,
            retrieval_filters={"topic": topic, "risk_level": risk_level},
            reason_context=", ".join(reasons),
        )


query_builder = PersonalizedQueryBuilder()
