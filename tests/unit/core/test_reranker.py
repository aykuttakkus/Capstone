from __future__ import annotations

from server.app.core.retrieval.reranker import EvidenceReranker
from tests.factories.retrieval import build_scored_chunk


def test_reranker_prefers_stronger_topic_and_confidence() -> None:
    reranker = EvidenceReranker(top_k=2, max_chars=1000)
    query = "tell me about anxiety and stress"
    weak = build_scored_chunk("weak", topic="low_mood", score=0.8, content="Low mood can feel heavy.", keywords=["mood"],)
    strong = build_scored_chunk(
        "strong",
        topic="stress_anxiety",
        score=0.7,
        content="Anxiety and stress can disrupt sleep and concentration.",
        keywords=["anxiety", "stress", "sleep"],
        confidence=0.98,
    )

    results = reranker.rerank(query, [weak, strong], topic="stress_anxiety")

    assert results[0].chunk.id == "strong"
    assert len(results) == 2


def test_reranker_respects_context_budget() -> None:
    reranker = EvidenceReranker(top_k=3, max_chars=120)
    query = "stress and sleep"
    chunks = [
        build_scored_chunk(f"c{i}", topic="burnout_sleep", score=1.0 - (i * 0.1), content="x" * 100, keywords=["stress", "sleep"], confidence=0.9)
        for i in range(4)
    ]

    results = reranker.rerank(query, chunks, topic="burnout_sleep")

    assert 1 <= len(results) <= 2
    assert sum(len(item.chunk.content) + len(item.chunk.title) for item in results) <= 120 + 100
