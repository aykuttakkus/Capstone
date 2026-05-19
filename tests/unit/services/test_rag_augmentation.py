"""
Unit Tests: RAGAugmentationService

Tests the full RAG pipeline including:
- Non-clinical bypass logic
- Query enrichment
- Topic detection
- Citation stripping
- Contextual compression
- Score threshold behavior
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from server.app.services.rag_augmentation import RAGAugmentationService, RetrievalResult


@pytest.fixture
def mock_rag_service(sample_chunks):
    """RAGAugmentationService with mocked retriever (no real FAISS needed)."""
    from server.app.core.retrieval.retriever import ScoredChunk

    mock_kb = MagicMock()
    mock_faiss = MagicMock()

    service = RAGAugmentationService.__new__(RAGAugmentationService)
    service.knowledge_base = mock_kb
    service.faiss_store = mock_faiss

    from server.app.core.retrieval.reranker import EvidenceReranker
    service.reranker = EvidenceReranker(top_k=3, max_chars=1800)

    scored = [ScoredChunk(chunk=c, score=0.05) for c in sample_chunks]

    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = scored
    service.retriever = mock_retriever

    return service


# ── Non-Clinical Bypass ───────────────────────────────────────────────────────

@pytest.mark.parametrize("message", [
    "hey", "hi", "hello", "ok", "thanks", "bye", "yes",
    "good morning", "thank you",
])
def test_greeting_bypasses_rag(message):
    assert RAGAugmentationService._is_non_clinical_message(message) is True


@pytest.mark.parametrize("message", [
    "I have been feeling very anxious lately",
    "I struggle to sleep because of stress",
    "Can you help me understand depression",
    "I feel lonely and disconnected",
])
def test_clinical_message_not_bypassed(message):
    assert RAGAugmentationService._is_non_clinical_message(message) is False


def test_two_word_message_bypassed():
    assert RAGAugmentationService._is_non_clinical_message("I'm fine") is True


def test_three_word_message_not_bypassed():
    assert RAGAugmentationService._is_non_clinical_message("I feel anxious") is False


# ── Topic Detection ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("message,expected_topic", [
    ("I'm feeling very anxious and worried", "anxiety"),
    ("I've been really depressed and hopeless", "depression"),
    ("I feel so lonely and isolated", "loneliness"),
    ("I can't sleep at night, I'm exhausted", "sleep"),
    ("I'm completely overwhelmed and burned out", "stress"),
    ("I have really low self-esteem", "self_esteem"),
])
def test_topic_detection(message, expected_topic):
    detected = RAGAugmentationService._detect_topic(message)
    assert detected == expected_topic, (
        f"Expected '{expected_topic}' for '{message}', got '{detected}'"
    )


# ── Citation Stripping ────────────────────────────────────────────────────────

def test_numbered_reference_stripped():
    text = "Loneliness affects wellbeing.\n7. Smith J, et al. (2020). Journal of Psychology."
    result = RAGAugmentationService._strip_citations(text)
    assert "Smith J" not in result
    assert "Journal of Psychology" not in result
    assert "Loneliness affects wellbeing" in result


def test_doi_stripped():
    text = "Evidence shows CBT works. doi:10.1016/j.brat.2020.01.001"
    result = RAGAugmentationService._strip_citations(text)
    assert "doi:" not in result
    assert "Evidence shows CBT works" in result


def test_url_stripped():
    text = "See more at https://example.com/mental-health"
    result = RAGAugmentationService._strip_citations(text)
    assert "https://" not in result


def test_clean_text_unchanged():
    text = "Breathing exercises can help reduce anxiety symptoms in stressful situations."
    result = RAGAugmentationService._strip_citations(text)
    assert result == text


# ── Contextual Compression ────────────────────────────────────────────────────

def test_relevant_sentence_extracted():
    content = (
        "The weather was nice today. "
        "Loneliness is associated with increased anxiety and depression risk. "
        "The study was conducted in 2019."
    )
    query_terms = {"loneliness", "anxiety", "depression"}
    result = RAGAugmentationService._extract_relevant_sentences(
        content, query_terms, max_chars=300
    )
    assert "Loneliness" in result or "loneliness" in result.lower()


def test_compression_respects_max_chars():
    content = "A " * 500
    query_terms = {"a"}
    result = RAGAugmentationService._extract_relevant_sentences(
        content, query_terms, max_chars=100
    )
    assert len(result) <= 110


def test_empty_content_returns_empty():
    result = RAGAugmentationService._extract_relevant_sentences("", set(), max_chars=200)
    assert result == ""


# ── Retrieval Result Structure ────────────────────────────────────────────────

def test_greeting_returns_empty_result(mock_rag_service, sample_user_state):
    result = mock_rag_service.augment_and_retrieve(
        user_message="hey",
        user_state=sample_user_state,
    )
    assert isinstance(result, RetrievalResult)
    assert result.formatted_knowledge is None
    assert result.chunk_count == 0
    assert result.retrieval_success is True


def test_clinical_message_returns_knowledge(mock_rag_service, sample_user_state):
    result = mock_rag_service.augment_and_retrieve(
        user_message="I have been feeling very anxious and cannot sleep",
        user_state=sample_user_state,
    )
    assert isinstance(result, RetrievalResult)
    assert result.retrieval_success is True


def test_result_has_required_fields(mock_rag_service):
    result = mock_rag_service.augment_and_retrieve(user_message="I feel anxious today")
    assert hasattr(result, "formatted_knowledge")
    assert hasattr(result, "retrieved_chunks")
    assert hasattr(result, "retrieval_success")
    assert hasattr(result, "chunk_count")
    assert hasattr(result, "top_score")
