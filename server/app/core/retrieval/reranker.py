from __future__ import annotations

from dataclasses import dataclass

from server.app.core.retrieval.retriever import ScoredChunk, topic_alignment_score
from server.app.utils.text import fuzzy_token_overlap, tokenize


@dataclass(slots=True)
class RerankDecision:
    chunk_id: str
    score: float
    reason: str


class EvidenceReranker:
    def __init__(self, top_k: int = 3, max_chars: int = 1200) -> None:
        self.top_k = top_k
        self.max_chars = max_chars

    def _score(self, query: str, item: ScoredChunk, topic: str | None = None) -> float:
        query_terms = set(tokenize(query))
        chunk_terms = set(tokenize(f"{item.chunk.title} {item.chunk.content} {' '.join(item.chunk.keywords)}"))
        overlap = len(query_terms & chunk_terms)
        fuzzy = fuzzy_token_overlap(query_terms, chunk_terms)
        alignment = topic_alignment_score(topic, item.chunk.topic)
        confidence = min(max(item.chunk.confidence, 0.0), 1.0)
        source_bonus = 0.0
        if item.chunk.source_kind == "safety_reference":
            source_bonus += 0.12
        elif item.chunk.source_kind == "intervention_manual":
            source_bonus += 0.08
        language_bonus = 0.05 if item.chunk.language == "en" else 0.07
        return item.score + (0.15 * overlap) + (0.10 * fuzzy) + (0.18 * alignment) + (0.12 * confidence) + source_bonus + language_bonus

    def rerank(self, query: str, retrievals: list[ScoredChunk], topic: str | None = None) -> list[ScoredChunk]:
        if not retrievals:
            return []

        ranked = sorted(
            retrievals,
            key=lambda item: (self._score(query, item, topic=topic), item.score, topic_alignment_score(topic, item.chunk.topic), item.chunk.id),
            reverse=True,
        )

        selected: list[ScoredChunk] = []
        used_chars = 0
        for item in ranked:
            chunk_chars = len(item.chunk.title) + len(item.chunk.content) + len(" ".join(item.chunk.keywords))
            if selected and (len(selected) >= self.top_k or used_chars + chunk_chars > self.max_chars):
                break
            selected.append(item)
            used_chars += chunk_chars

        return selected or ranked[: self.top_k]


reranker = EvidenceReranker()
