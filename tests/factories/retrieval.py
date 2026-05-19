from __future__ import annotations

from server.app.core.retrieval.corpus import KnowledgeBase, KnowledgeChunk
from server.app.core.retrieval.retriever import ScoredChunk


def build_chunk(
    chunk_id: str,
    *,
    topic: str = "stress_anxiety",
    title: str | None = None,
    content: str | None = None,
    keywords: list[str] | None = None,
    source_kind: str = "user_corpus",
    language: str = "en",
    confidence: float = 1.0,
    allowed_use: list[str] | None = None,
    not_allowed: list[str] | None = None,
    risk_level: str = "none",
    content_type: str = "psychoeducation",
    evidence_level: str = "educational",
    clinical_scope: str = "psychoeducation_only",
    review_required: bool = False,
    last_reviewed: str | None = None,
) -> KnowledgeChunk:
    return KnowledgeChunk(
        id=chunk_id,
        title=title or f"Title {chunk_id}",
        topic=topic,
        source="Test corpus",
        content=content or "Stress can affect sleep, focus, and energy.",
        keywords=keywords or ["stress", "sleep"],
        source_kind=source_kind,
        language=language,
        confidence=confidence,
        allowed_use=allowed_use or ["psychoeducation", "coping_strategy", "symptom_exploration", "emotional_support"],
        not_allowed=not_allowed or ["diagnosis", "medication_advice"],
        risk_level=risk_level,
        content_type=content_type,
        evidence_level=evidence_level,
        clinical_scope=clinical_scope,
        review_required=review_required,
        last_reviewed=last_reviewed,
    )


def build_scored_chunk(
    chunk_id: str,
    *,
    topic: str = "stress_anxiety",
    score: float = 0.9,
    content: str | None = None,
    keywords: list[str] | None = None,
    source_kind: str = "user_corpus",
    language: str = "en",
    confidence: float = 1.0,
    allowed_use: list[str] | None = None,
    not_allowed: list[str] | None = None,
    risk_level: str = "none",
    evidence_level: str = "educational",
    clinical_scope: str = "psychoeducation_only",
    content_type: str = "psychoeducation",
) -> ScoredChunk:
    return ScoredChunk(
        chunk=build_chunk(
            chunk_id,
            topic=topic,
            content=content,
            keywords=keywords,
            source_kind=source_kind,
            language=language,
            confidence=confidence,
            allowed_use=allowed_use,
            not_allowed=not_allowed,
            risk_level=risk_level,
            evidence_level=evidence_level,
            clinical_scope=clinical_scope,
            content_type=content_type,
        ),
        score=score,
    )


def build_small_knowledge_base() -> KnowledgeBase:
    return KnowledgeBase(
        chunks=[
            build_chunk(
                "stress-001",
                topic="stress_anxiety",
                title="Stress basics",
                content="Stress can disrupt sleep, concentration, and energy levels.",
                keywords=["stress", "sleep", "energy"],
            ),
            build_chunk(
                "sleep-001",
                topic="burnout_sleep",
                title="Sleep overview",
                content="Sleep quality and stress influence each other over time.",
                keywords=["sleep", "stress", "fatigue"],
            ),
            build_chunk(
                "mood-001",
                topic="low_mood",
                title="Low mood overview",
                content="Low mood can affect motivation, energy, and daily functioning.",
                keywords=["mood", "energy", "sad"],
            ),
        ]
    )
