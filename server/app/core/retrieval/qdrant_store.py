from __future__ import annotations

from dataclasses import dataclass
from dataclasses import asdict
from typing import Any

from server.app.core.retrieval.corpus import KnowledgeBase, KnowledgeChunk

try:
    from qdrant_client import QdrantClient  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    QdrantClient = None  # type: ignore[assignment]


@dataclass(slots=True)
class QdrantRecord:
    chunk: KnowledgeChunk
    score: float


class QdrantStore:
    def __init__(self, url: str, collection_name: str) -> None:
        self.url = url
        self.collection_name = collection_name
        self._client = QdrantClient(url=url) if QdrantClient is not None else None

    @property
    def available(self) -> bool:
        return self._client is not None

    def build(self, knowledge_base: KnowledgeBase, embedder) -> None:  # type: ignore[no-untyped-def]
        if self._client is None:
            return

        vectors = embedder.embed_many([
            f"{chunk.title} {chunk.content} {' '.join(chunk.keywords)}" for chunk in knowledge_base.chunks
        ])

        try:
            self._client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config={"size": len(vectors[0]) if vectors else embedder.dimension, "distance": "Cosine"},
            )
            points = []
            for chunk, vector in zip(knowledge_base.chunks, vectors):
                points.append(
                    {
                        "id": chunk.id,
                        "vector": vector,
                        "payload": {
                            **asdict(chunk),
                        },
                    }
                )
            if points:
                self._client.upsert(collection_name=self.collection_name, points=points)
        except Exception:
            return

    def search(self, query_embedding: list[float], topic: str | None = None, k: int = 5) -> list[tuple[KnowledgeChunk, float]]:
        return self.search_with_filters(query_embedding, topic=topic, k=k)

    @staticmethod
    def _matches_filters(
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

    def search_with_filters(
        self,
        query_embedding: list[float],
        topic: str | None = None,
        k: int = 5,
        *,
        source_kind: str | None = None,
        language: str | None = None,
        min_confidence: float | None = None,
    ) -> list[tuple[KnowledgeChunk, float]]:
        if self._client is None:
            return []

        try:
            results = self._client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=k,
                with_payload=True,
            )
        except Exception:
            return []

        scored: list[tuple[KnowledgeChunk, float]] = []
        for item in results:
            payload: dict[str, Any] = item.payload or {}
            chunk = KnowledgeChunk.from_dict(payload)
            if not self._matches_filters(chunk, topic=topic, source_kind=source_kind, language=language, min_confidence=min_confidence):
                continue
            scored.append((chunk, float(item.score or 0.0)))
        return scored
