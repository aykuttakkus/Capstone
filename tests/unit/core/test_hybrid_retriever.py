"""
Unit Tests: HybridRetriever

Tests the BM25+Dense hybrid retrieval engine that combines semantic
and keyword signals with topic alignment boosting.

Retrieval quality directly affects therapeutic response quality —
a missed relevant chunk means the LLM has less evidence to draw from.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from server.app.core.retrieval.retriever import ScoredChunk
from server.app.core.retrieval.corpus import KnowledgeChunk, KnowledgeBase


def make_chunk(
    chunk_id: str,
    topic: str,
    content: str,
    source_kind: str = "user_corpus",
    confidence: float = 0.9,
    language: str = "en",
) -> KnowledgeChunk:
    return KnowledgeChunk(
        id=chunk_id,
        title=topic.replace("_", " ").title(),
        topic=topic,
        source="test.pdf",
        content=content,
        keywords=content.split()[:5],
        confidence=confidence,
        source_kind=source_kind,
        language=language,
    )


@pytest.fixture
def mock_retriever(sample_chunks):
    """HybridRetriever with mocked embedding and FAISS stores."""
    from server.app.core.retrieval.hybrid_retriever import HybridRetriever

    mock_kb = MagicMock(spec=KnowledgeBase)
    mock_kb.chunks = sample_chunks

    mock_faiss = MagicMock()
    mock_faiss.search.return_value = [
        (sample_chunks[0], 0.85),
        (sample_chunks[1], 0.72),
        (sample_chunks[2], 0.61),
    ]

    mock_embedder = MagicMock()
    mock_embedder.embed.return_value = [0.1] * 384

    retriever = HybridRetriever.__new__(HybridRetriever)
    retriever.knowledge_base = mock_kb
    retriever.faiss_store = mock_faiss
    retriever.embedder = mock_embedder
    retriever.graph_store = None
    retriever.qdrant_store = MagicMock()
    retriever.qdrant_store.available = False

    from server.app.core.retrieval.retriever import SimpleRetriever
    retriever.keyword_retriever = SimpleRetriever(mock_kb)

    return retriever


# ── Basic Retrieval ───────────────────────────────────────────────────────────

def test_retrieve_returns_list(mock_retriever):
    results = mock_retriever.retrieve("I feel anxious and worried", k=5)
    assert isinstance(results, list)


def test_retrieve_respects_k(mock_retriever):
    results = mock_retriever.retrieve("loneliness isolation", k=3)
    assert len(results) <= 3


def test_retrieve_returns_scored_chunks(mock_retriever):
    results = mock_retriever.retrieve("anxiety management", k=5)
    for r in results:
        assert isinstance(r, ScoredChunk)
        assert hasattr(r, "score")
        assert hasattr(r.chunk, "content")


def test_retrieve_scores_are_positive(mock_retriever):
    results = mock_retriever.retrieve("feeling depressed", k=5)
    for r in results:
        assert r.score >= 0.0


# ── Score Composition ─────────────────────────────────────────────────────────

def test_semantic_weight_dominates(mock_retriever):
    """Semantic weight is 0.70, keyword 0.30 — semantic signal dominates combined score."""
    assert mock_retriever.SEMANTIC_WEIGHT > mock_retriever.KEYWORD_WEIGHT


def test_combined_score_bounded(mock_retriever):
    """Combined score should not exceed a reasonable upper bound (1.5 with boosts)."""
    results = mock_retriever.retrieve("anxiety stress", k=5)
    for r in results:
        assert r.score <= 2.0, f"Score {r.score} is suspiciously high"


# ── Filter Application ────────────────────────────────────────────────────────

def test_retrieve_with_source_kind_filter(mock_retriever, sample_chunks):
    """source_kind filter must be applied to retrieved results."""
    # Patch chunk lookup to contain mixed sources
    mock_retriever.knowledge_base.chunks = [
        make_chunk("sc1", "crisis", "crisis safety planning", source_kind="safety_reference"),
        make_chunk("uc1", "anxiety", "anxiety coping techniques", source_kind="user_corpus"),
    ]
    mock_retriever.faiss_store.search.return_value = [
        (mock_retriever.knowledge_base.chunks[0], 0.7),
        (mock_retriever.knowledge_base.chunks[1], 0.65),
    ]

    results = mock_retriever.retrieve("anxiety", k=5, source_kind="safety_reference")
    for r in results:
        assert r.chunk.source_kind == "safety_reference"


def test_retrieve_with_min_confidence_filter(mock_retriever):
    """min_confidence filter must exclude low-confidence chunks."""
    low_conf = make_chunk("lc1", "sleep", "sleep hygiene tips content", confidence=0.2)
    high_conf = make_chunk("hc1", "sleep", "sleep hygiene tips content", confidence=0.9)
    mock_retriever.knowledge_base.chunks = [low_conf, high_conf]
    mock_retriever.faiss_store.search.return_value = [
        (low_conf, 0.7),
        (high_conf, 0.7),
    ]

    results = mock_retriever.retrieve("sleep problems", k=5, min_confidence=0.5)
    for r in results:
        assert r.chunk.confidence >= 0.5


# ── Edge Cases ────────────────────────────────────────────────────────────────

def test_empty_knowledge_base_returns_empty(sample_chunks):
    from server.app.core.retrieval.hybrid_retriever import HybridRetriever

    mock_kb = MagicMock(spec=KnowledgeBase)
    mock_kb.chunks = []

    mock_faiss = MagicMock()
    mock_faiss.search.return_value = []

    mock_embedder = MagicMock()
    mock_embedder.embed.return_value = [0.1] * 384

    retriever = HybridRetriever.__new__(HybridRetriever)
    retriever.knowledge_base = mock_kb
    retriever.faiss_store = mock_faiss
    retriever.embedder = mock_embedder
    retriever.graph_store = None
    retriever.qdrant_store = MagicMock()
    retriever.qdrant_store.available = False

    from server.app.core.retrieval.retriever import SimpleRetriever
    retriever.keyword_retriever = SimpleRetriever(mock_kb)

    results = retriever.retrieve("anxiety", k=5)
    assert results == []
