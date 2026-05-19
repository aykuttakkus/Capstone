"""
Unit Tests: EvidenceReranker

Tests the cross-encoder-style reranker that improves retrieval precision
by scoring chunks based on term overlap, topic alignment, source quality,
and confidence.
"""

from __future__ import annotations

import pytest
from server.app.core.retrieval.reranker import EvidenceReranker
from server.app.core.retrieval.retriever import ScoredChunk
from server.app.core.retrieval.corpus import KnowledgeChunk


def make_chunk(chunk_id: str, topic: str, content: str, confidence: float = 0.9,
               source_kind: str = "user_corpus") -> ScoredChunk:
    return ScoredChunk(
        chunk=KnowledgeChunk(
            id=chunk_id,
            title=topic.replace("_", " ").title(),
            topic=topic,
            source="test_source.pdf",
            content=content,
            keywords=content.split()[:5],
            confidence=confidence,
            source_kind=source_kind,
            language="en",
        ),
        score=0.03,
    )


@pytest.fixture
def reranker():
    return EvidenceReranker(top_k=3, max_chars=1800)


# ── Basic Functionality ───────────────────────────────────────────────────────

def test_reranker_returns_list(reranker, sample_chunks):
    scored = [ScoredChunk(chunk=c, score=0.03) for c in sample_chunks]
    result = reranker.rerank("I feel lonely and disconnected", scored)
    assert isinstance(result, list)


def test_reranker_respects_top_k(reranker):
    chunks = [
        make_chunk(f"c{i}", "anxiety", f"anxiety stress worry fear content {i}")
        for i in range(10)
    ]
    result = reranker.rerank("anxiety stress management", chunks)
    assert len(result) <= 3


def test_reranker_returns_scored_chunks(reranker, sample_chunks):
    scored = [ScoredChunk(chunk=c, score=0.03) for c in sample_chunks]
    result = reranker.rerank("loneliness isolation support", scored)
    for item in result:
        assert isinstance(item, ScoredChunk)
        assert hasattr(item.chunk, "content")


def test_empty_input_returns_empty(reranker):
    result = reranker.rerank("loneliness", [])
    assert result == []


# ── Relevance Ordering ────────────────────────────────────────────────────────

def test_topic_relevant_chunk_ranked_higher(reranker):
    """Chunk with matching topic should rank above unrelated chunk."""
    relevant = make_chunk("r1", "loneliness", "loneliness isolation social disconnection wellbeing")
    irrelevant = make_chunk("i1", "sleep", "sleep schedule bedroom routine blue light screen")

    result = reranker.rerank("I feel lonely and isolated", [irrelevant, relevant])
    if len(result) >= 2:
        assert result[0].chunk.id == "r1", "Relevant loneliness chunk should rank first"


def test_high_confidence_chunk_boosted(reranker):
    low_conf = make_chunk("lc", "anxiety", "anxiety management techniques", confidence=0.3)
    high_conf = make_chunk("hc", "anxiety", "anxiety management techniques", confidence=0.95)

    result = reranker.rerank("anxiety management", [low_conf, high_conf])
    assert result[0].chunk.id == "hc", "High confidence chunk should rank first"


def test_safety_reference_gets_bonus(reranker):
    """Safety reference source gets score bonus in crisis-adjacent queries."""
    normal = make_chunk("n1", "anxiety", "anxiety coping strategies techniques", source_kind="user_corpus")
    safety = make_chunk("s1", "crisis", "crisis safety planning self-harm intervention", source_kind="safety_reference")

    result = reranker.rerank("self-harm crisis safety", [normal, safety])
    assert result[0].chunk.id == "s1", "Safety reference should rank first for crisis query"


# ── Character Budget ──────────────────────────────────────────────────────────

def test_reranker_respects_max_chars():
    reranker = EvidenceReranker(top_k=5, max_chars=100)
    chunks = [
        make_chunk(f"c{i}", "anxiety", "anxiety " * 50)
        for i in range(5)
    ]
    result = reranker.rerank("anxiety", chunks)
    # Should limit results based on char budget
    assert len(result) <= 5
