from __future__ import annotations

from dataclasses import dataclass

import server.app.core.retrieval.qdrant_store as qdrant_module
from server.app.core.retrieval.corpus import KnowledgeBase
from tests.factories.retrieval import build_small_knowledge_base


@dataclass
class FakePoint:
    id: str
    vector: list[float]
    payload: dict


@dataclass
class FakeResult:
    payload: dict
    score: float


class FakeQdrantClient:
    def __init__(self, *args, **kwargs):
        self.built = False
        self.points: list[FakePoint] = []

    def recreate_collection(self, *args, **kwargs):
        self.built = True

    def upsert(self, collection_name, points):
        self.points.extend(FakePoint(**point) for point in points)

    def search(self, *args, **kwargs):
        return []


def test_qdrant_store_builds_collection_and_points(monkeypatch) -> None:
    monkeypatch.setattr(qdrant_module, "QdrantClient", FakeQdrantClient, raising=False)

    store = qdrant_module.QdrantStore("http://localhost:6333", "calma_chunks")
    kb = build_small_knowledge_base()

    class DummyEmbedder:
        dimension = 32

        def embed_many(self, texts):
            return [[0.1] * self.dimension for _ in texts]

    store.build(kb, DummyEmbedder())

    assert store._client.built is True
    assert len(store._client.points) == len(kb.chunks)
    assert store._client.points[0].payload["topic"]


def test_qdrant_store_filters_results_by_metadata(monkeypatch) -> None:
    class FilteringQdrantClient(FakeQdrantClient):
        def search(self, *args, **kwargs):
            return [
                FakeResult(payload={"id": "a", "title": "A", "topic": "stress_anxiety", "source": "X", "content": "stress", "keywords": ["stress"], "source_kind": "safety_reference", "language": "en", "confidence": 0.98}, score=0.9),
                FakeResult(payload={"id": "b", "title": "B", "topic": "low_mood", "source": "X", "content": "mood", "keywords": ["mood"], "source_kind": "user_corpus", "language": "en", "confidence": 0.5}, score=0.8),
            ]

    monkeypatch.setattr(qdrant_module, "QdrantClient", FilteringQdrantClient, raising=False)

    store = qdrant_module.QdrantStore("http://localhost:6333", "calma_chunks")
    results = store.search_with_filters(
        [0.1, 0.1, 0.1],
        topic="stress_anxiety",
        k=5,
        source_kind="safety_reference",
        language="en",
        min_confidence=0.9,
    )

    assert len(results) == 1
    assert results[0][0].id == "a"
