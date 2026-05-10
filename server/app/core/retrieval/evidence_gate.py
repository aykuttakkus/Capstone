from __future__ import annotations

import os

from server.app.core.retrieval.retriever import ScoredChunk, topic_matches


class EvidenceGate:
    def __init__(self, min_score: float | None = None, min_chunks: int | None = None) -> None:
        self.min_score = min_score if min_score is not None else float(os.getenv("EVIDENCE_MIN_SCORE", "0.22"))
        self.min_chunks = min_chunks if min_chunks is not None else int(os.getenv("EVIDENCE_MIN_CHUNKS", "1"))

    def has_enough_evidence(self, results: list[ScoredChunk], topic: str | None = None) -> bool:
        if not results:
            return False
        if topic in (None, "", "general"):
            candidates = results
        else:
            candidates = [r for r in results if topic_matches(topic, r.chunk.topic)]
            if not candidates:
                return False

        above = sum(1 for r in candidates if r.score >= self.min_score)
        return above >= self.min_chunks

    def gate_score(self, results: list[ScoredChunk]) -> float:
        return results[0].score if results else 0.0
