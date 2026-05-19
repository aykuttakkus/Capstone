"""
Integration Tests: RAG Pipeline Quality

Tests that the full RAG pipeline (query enrichment → retrieval → reranking
→ compression → LLM injection) operates correctly as an integrated unit.

These tests use mocked retrievers with controlled corpora so results
are deterministic without needing actual FAISS indices loaded.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from server.app.services.rag_augmentation import RAGAugmentationService
from server.app.core.retrieval.retriever import ScoredChunk
from server.app.core.retrieval.reranker import EvidenceReranker


@pytest.fixture
def rag_service(sample_chunks):
    """RAG service with mocked retriever, returning all sample chunks."""
    service = RAGAugmentationService.__new__(RAGAugmentationService)
    service.knowledge_base = MagicMock()
    service.faiss_store = MagicMock()
    service.reranker = EvidenceReranker(top_k=3, max_chars=1800)

    scored = [ScoredChunk(chunk=c, score=0.05) for c in sample_chunks]
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = scored
    service.retriever = mock_retriever

    return service


# ── Non-clinical bypass ───────────────────────────────────────────────────────

@pytest.mark.parametrize("message", ["hi", "hello", "hey", "thanks", "ok", "bye"])
def test_greeting_returns_empty_context(rag_service, message):
    """Greetings must bypass RAG entirely — no chunks retrieved."""
    result = rag_service.augment_and_retrieve(user_message=message)
    assert result.chunk_count == 0
    assert result.formatted_knowledge is None


def test_two_word_message_bypasses_rag(rag_service):
    """Very short messages without clinical signals should not trigger retrieval."""
    result = rag_service.augment_and_retrieve(user_message="I'm fine")
    assert result.chunk_count == 0


# ── Clinical message triggers retrieval ──────────────────────────────────────

@pytest.mark.parametrize("message", [
    "I have been feeling really anxious and can't stop worrying",
    "I feel hopeless and have no energy for anything",
    "I've been struggling with sleep problems for weeks",
    "I feel completely alone and disconnected from everyone",
])
def test_clinical_message_triggers_retrieval(rag_service, message):
    """Clinical messages with distress signals must trigger RAG retrieval."""
    result = rag_service.augment_and_retrieve(user_message=message)
    # Retrieval should have been attempted (retriever.retrieve called)
    assert rag_service.retriever.retrieve.called


# ── Chunk count cap ───────────────────────────────────────────────────────────

def test_at_most_three_chunks_returned(rag_service):
    """LLM context must contain at most 3 chunks to prevent context bloat."""
    result = rag_service.augment_and_retrieve(
        user_message="I feel anxious, lonely, stressed, and hopeless all at once"
    )
    assert result.chunk_count <= 3


# ── Citation-free output ──────────────────────────────────────────────────────

def test_no_doi_in_formatted_knowledge(rag_service):
    """Academic DOIs must never appear in LLM-injected knowledge."""
    result = rag_service.augment_and_retrieve(
        user_message="I've been struggling with anxiety and depression"
    )
    if result.formatted_knowledge:
        assert "doi:" not in result.formatted_knowledge.lower()
        assert "doi.org" not in result.formatted_knowledge.lower()


def test_no_numbered_references_in_formatted_knowledge(rag_service):
    """Academic reference lists (1. Author...) must not appear in RAG output."""
    import re
    result = rag_service.augment_and_retrieve(
        user_message="I've been feeling very depressed and hopeless"
    )
    if result.formatted_knowledge:
        assert not re.search(r"\n\d+\.\s+[A-Z][a-z]", result.formatted_knowledge), (
            "Numbered academic citation found in RAG output"
        )


# ── Query enrichment ──────────────────────────────────────────────────────────

def test_query_enriched_with_user_state(rag_service, sample_user_state):
    """When user state is provided, query must incorporate state signals."""
    captured = []
    original = rag_service.retriever.retrieve

    def capture(q, **kwargs):
        captured.append(q)
        return original(q, **kwargs)

    rag_service.retriever.retrieve = capture

    rag_service.augment_and_retrieve(
        user_message="I feel anxious",
        user_state=sample_user_state,
    )

    if captured:
        q = captured[0].lower()
        assert any(term in q for term in ["anxiety", "social", "isolation", "stress"]), (
            f"Query not enriched with user state signals: {captured[0]}"
        )


# ── Result structure ──────────────────────────────────────────────────────────

def test_retrieval_result_has_expected_fields(rag_service):
    result = rag_service.augment_and_retrieve(
        user_message="I've been feeling very anxious and sad"
    )
    assert hasattr(result, "chunk_count")
    assert hasattr(result, "formatted_knowledge")
    assert hasattr(result, "retrieval_success")
    assert hasattr(result, "top_score")


def test_top_score_positive_when_chunks_found(rag_service):
    result = rag_service.augment_and_retrieve(
        user_message="I've been struggling with severe anxiety for weeks"
    )
    if result.retrieval_success and result.chunk_count > 0:
        assert result.top_score > 0


# ── Graceful failure ──────────────────────────────────────────────────────────

def test_retrieval_failure_does_not_raise(sample_chunks):
    """If retriever raises, RAG should degrade gracefully (return empty)."""
    service = RAGAugmentationService.__new__(RAGAugmentationService)
    service.knowledge_base = MagicMock()
    service.faiss_store = MagicMock()
    service.reranker = EvidenceReranker(top_k=3, max_chars=1800)

    mock_retriever = MagicMock()
    mock_retriever.retrieve.side_effect = RuntimeError("Index not found")
    service.retriever = mock_retriever

    result = service.augment_and_retrieve(
        user_message="I feel very anxious and stressed"
    )
    assert result is not None
    assert result.chunk_count == 0
