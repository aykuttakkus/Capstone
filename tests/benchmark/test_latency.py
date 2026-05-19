"""
Benchmark Tests: System Latency and Performance

Measures wall-clock latency of the RAG pipeline components to ensure
the system meets response-time SLAs suitable for a mental health context.

In mental health conversations, response latency affects therapeutic alliance.
Users experiencing distress should not wait > 3 seconds for a reply.

SLA thresholds (CPU baseline, no GPU):
- Non-clinical bypass (greeting): < 5 ms
- RAG query enrichment: < 50 ms
- Reranker (3 chunks): < 20 ms
- Full RAG pipeline (mocked retriever): < 200 ms

Note: These are synchronous component tests.
LLM latency (Ollama/Mistral) is excluded — measured separately.
"""

from __future__ import annotations

import time
import pytest
from unittest.mock import MagicMock

from server.app.services.rag_augmentation import RAGAugmentationService
from server.app.core.retrieval.retriever import ScoredChunk
from server.app.core.retrieval.reranker import EvidenceReranker


@pytest.fixture
def fast_rag_service(sample_chunks):
    """RAG service with pre-loaded sample chunks (no I/O during test)."""
    service = RAGAugmentationService.__new__(RAGAugmentationService)
    service.knowledge_base = MagicMock()
    service.faiss_store = MagicMock()
    service.reranker = EvidenceReranker(top_k=3, max_chars=1800)

    scored = [ScoredChunk(chunk=c, score=0.05) for c in sample_chunks]
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = scored
    service.retriever = mock_retriever

    return service


# ── Non-clinical bypass latency ───────────────────────────────────────────────

def test_greeting_bypass_under_5ms(fast_rag_service):
    """Greeting non-clinical bypass must return in < 5 ms (no retrieval I/O)."""
    start = time.perf_counter()
    fast_rag_service.augment_and_retrieve(user_message="hello")
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 5.0, f"Greeting bypass took {elapsed_ms:.1f} ms (expected < 5 ms)"


# ── Reranker latency ──────────────────────────────────────────────────────────

def test_reranker_3_chunks_under_20ms(sample_chunks):
    """Reranking 3 chunks must complete in < 20 ms."""
    reranker = EvidenceReranker(top_k=3, max_chars=1800)
    scored = [ScoredChunk(chunk=c, score=0.05) for c in sample_chunks[:3]]

    start = time.perf_counter()
    reranker.rerank("I feel anxious and lonely", scored)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 20.0, f"Reranker took {elapsed_ms:.1f} ms (expected < 20 ms)"


def test_reranker_10_chunks_under_50ms():
    """Reranking 10 chunks (e.g. large retrieval set) must complete < 50 ms."""
    from server.app.core.retrieval.corpus import KnowledgeChunk
    reranker = EvidenceReranker(top_k=5, max_chars=2500)

    chunks = [
        ScoredChunk(
            chunk=KnowledgeChunk(
                id=f"c{i}",
                title=f"Chunk {i}",
                topic="anxiety",
                source="test.pdf",
                content=f"anxiety stress management coping techniques practice {i}",
                keywords=["anxiety", "stress", "coping"],
                confidence=0.8,
            ),
            score=0.05,
        )
        for i in range(10)
    ]

    start = time.perf_counter()
    reranker.rerank("anxiety stress management", chunks)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 50.0, f"Reranker (10 chunks) took {elapsed_ms:.1f} ms (expected < 50 ms)"


# ── Full RAG pipeline latency (mocked retriever) ──────────────────────────────

def test_full_rag_pipeline_under_200ms(fast_rag_service):
    """Full RAG pipeline (enrichment + retrieval call + rerank + format) < 200 ms.

    This excludes network I/O to the embedding model; the retriever is mocked.
    Represents the overhead Calma's own code adds on top of model inference.
    """
    start = time.perf_counter()
    fast_rag_service.augment_and_retrieve(
        user_message="I've been struggling with anxiety and sleep problems"
    )
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 200.0, (
        f"Full RAG pipeline took {elapsed_ms:.1f} ms (expected < 200 ms). "
        "If this is consistently slow, profile _build_primary_query and _compress_and_format."
    )


# ── Repeated calls: no degradation ───────────────────────────────────────────

def test_no_degradation_over_10_calls(fast_rag_service):
    """Pipeline must not degrade over repeated calls (no memory leak / state accumulation)."""
    times = []
    for _ in range(10):
        start = time.perf_counter()
        fast_rag_service.augment_and_retrieve(
            user_message="I feel anxious and overwhelmed"
        )
        times.append((time.perf_counter() - start) * 1000)

    # Last call should not be dramatically slower than first
    assert times[-1] < times[0] * 5, (
        f"Pipeline degraded: first={times[0]:.1f} ms, last={times[-1]:.1f} ms"
    )

    # Average should stay under 200 ms
    avg = sum(times) / len(times)
    assert avg < 200.0, f"Average call time {avg:.1f} ms exceeds 200 ms SLA"
