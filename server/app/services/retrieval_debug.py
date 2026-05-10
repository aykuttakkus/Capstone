from __future__ import annotations

from server.app.core.retrieval.retriever import ScoredChunk, topic_alignment_score
from server.app.models.schemas.chat import RetrievalDiagnostic, SourceReference
from server.app.utils.text import tokenize


def _shared_terms(query: str, chunk_text: str) -> int:
    query_terms = set(tokenize(query))
    chunk_terms = set(tokenize(chunk_text))
    return len(query_terms & chunk_terms)


def _reason_tags(query: str, chunk: ScoredChunk, query_topic: str | None = None) -> tuple[list[str], int, str]:
    tags: list[str] = []
    alignment = topic_alignment_score(query_topic, chunk.chunk.topic)
    if alignment >= 1.0:
        tags.append("topic_match")
        alignment_label = "exact"
    elif alignment > 0:
        tags.append("topic_related")
        alignment_label = "related"
    else:
        alignment_label = "none"

    query_overlap = _shared_terms(query, f"{chunk.chunk.title} {chunk.chunk.content} {' '.join(chunk.chunk.keywords)}")
    if query_overlap > 0:
        tags.append("query_overlap")

    if chunk.score >= 0.8:
        tags.append("high_score")
    elif chunk.score >= 0.5:
        tags.append("medium_score")
    else:
        tags.append("low_score")

    if not tags:
        tags.append("fallback")

    return tags, query_overlap, alignment_label


def build_source_reference(query: str, chunk: ScoredChunk, rank: int, query_topic: str | None = None) -> SourceReference:
    tags, _, _ = _reason_tags(query, chunk, query_topic=query_topic)
    return SourceReference(
        title=chunk.chunk.title,
        source=chunk.chunk.source,
        topic=chunk.chunk.topic,
        score=round(chunk.score, 4),
        excerpt=chunk.chunk.content[:220].strip(),
        rank=rank,
        source_kind=chunk.chunk.source_kind,
        language=chunk.chunk.language,
        confidence=round(chunk.chunk.confidence, 4),
        section=chunk.chunk.section or None,
        page=chunk.chunk.page or None,
        reason_tags=tags,
    )


def build_retrieval_diagnostics(
    query: str,
    retrievals: list[ScoredChunk],
    query_topic: str | None = None,
) -> list[RetrievalDiagnostic]:
    diagnostics: list[RetrievalDiagnostic] = []
    for rank, item in enumerate(retrievals, start=1):
        tags, overlap, alignment = _reason_tags(query, item, query_topic=query_topic)
        diagnostics.append(
            RetrievalDiagnostic(
                rank=rank,
                chunk_id=item.chunk.id,
                title=item.chunk.title,
                topic=item.chunk.topic,
                score=round(item.score, 4),
                source_kind=item.chunk.source_kind,
                language=item.chunk.language,
                confidence=round(item.chunk.confidence, 4),
                topic_alignment=alignment,
                query_overlap=overlap,
                reason_tags=tags,
            )
        )
    return diagnostics
