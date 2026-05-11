from __future__ import annotations

from dataclasses import dataclass

from server.app.core.retrieval.corpus import KnowledgeBase, KnowledgeChunk
from server.app.utils.text import fuzzy_token_overlap, infer_language, tokenize


@dataclass(slots=True)
class ScoredChunk:
    chunk: KnowledgeChunk
    score: float


def normalize_topic_filter(query_topic: str | None, *, available_topics: set[str] | None = None) -> str | None:
    if query_topic is None:
        return None

    normalized = query_topic.strip().lower()
    if not normalized or normalized in {"general", "unknown", "none", "null"}:
        return None

    if not available_topics:
        return normalized

    normalized_topics = {
        topic.strip().lower()
        for topic in available_topics
        if topic and topic.strip()
    }
    if normalized in normalized_topics:
        return normalized

    query_parts = {part for part in normalized.split("_") if len(part) >= 3}
    if not query_parts:
        return None

    topic_parts = [{part for part in topic.split("_") if len(part) >= 3} for topic in normalized_topics]
    if any(query_parts & parts for parts in topic_parts):
        return normalized
    return None


def topic_matches(query_topic: str | None, chunk_topic: str) -> bool:
    normalized_topic = normalize_topic_filter(query_topic, available_topics={chunk_topic})
    if not normalized_topic:
        return True
    if chunk_topic == normalized_topic:
        return True
    query_parts = [part for part in normalized_topic.split("_") if part]
    return any(part in chunk_topic for part in query_parts)


def topic_alignment_score(query_topic: str | None, chunk_topic: str) -> float:
    normalized_topic = normalize_topic_filter(query_topic, available_topics={chunk_topic})
    if not normalized_topic:
        return 0.0
    if chunk_topic == normalized_topic:
        return 1.0
    if topic_matches(normalized_topic, chunk_topic):
        return 0.5
    return 0.0


class SimpleRetriever:
    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        self.knowledge_base = knowledge_base

    def _matches_filters(
        self,
        chunk: KnowledgeChunk,
        *,
        topic: str | None = None,
        source_kind: str | None = None,
        language: str | None = None,
        min_confidence: float | None = None,
    ) -> bool:
        if topic and chunk.topic != topic and not any(part in chunk.topic for part in topic.split("_") if part):
            return False
        if source_kind and chunk.source_kind != source_kind:
            return False
        if language and chunk.language != language:
            return False
        if min_confidence is not None and chunk.confidence < min_confidence:
            return False
        return True

    def retrieve(
        self,
        query: str,
        topic: str | None = None,
        k: int = 3,
        *,
        source_kind: str | None = None,
        language: str | None = None,
        min_confidence: float | None = None,
    ) -> list[ScoredChunk]:
        normalized_topic = normalize_topic_filter(topic, available_topics={chunk.topic for chunk in self.knowledge_base.chunks})
        query_terms = set(tokenize(query))
        topic_terms = set(tokenize(normalized_topic or ""))
        query_language = infer_language(query)
        scored: list[ScoredChunk] = []

        for chunk in self.knowledge_base.chunks:
            if not self._matches_filters(chunk, topic=normalized_topic, source_kind=source_kind, language=language, min_confidence=min_confidence):
                continue
            chunk_terms = set(tokenize(f"{chunk.title} {chunk.content} {' '.join(chunk.keywords)}"))
            overlap = len(query_terms & chunk_terms)
            fuzzy_overlap = fuzzy_token_overlap(query_terms, chunk_terms)
            keyword_tokens = set(tokenize(" ".join(chunk.keywords)))
            keyword_bonus = len(query_terms & keyword_tokens) * 2 + fuzzy_token_overlap(query_terms, keyword_tokens)
            topic_bonus = 3 if normalized_topic and chunk.topic == normalized_topic else 0
            topic_overlap = len(topic_terms & set(tokenize(chunk.topic)))
            language_bonus = 1 if chunk.language == query_language else 0
            score = float(overlap + fuzzy_overlap + keyword_bonus + topic_bonus + topic_overlap + language_bonus)
            scored.append(ScoredChunk(chunk=chunk, score=score))

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:k]
